# S-SEC-015: Block Timestamp Manipulation Detection
# Detects dangerous usage of block.timestamp in comparisons and critical logic
# block.timestamp can be manipulated by miners within certain bounds

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class BlockTimestampManipulationDetector(SolidityParserListener):
    """
    Detects dangerous usage of block.timestamp in comparisons and critical logic.
    
    This detector identifies:
    1. block.timestamp or 'now' used in require/assert statements
    2. block.timestamp in conditional comparisons
    3. block.timestamp in critical state changes
    
    False Positive Mitigation:
    - Allows simple time-lock patterns with sufficient time buffers (> 15 minutes)
    - Excludes view/pure functions
    - Ignores timestamp usage in events/logging
    - Allows timestamp for long-term time locks (days/weeks)
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None
        self.function_start_line = None
        self.is_view_or_pure = False
        self.current_statement_line = None
        
        # Timestamp sources
        self.timestamp_sources = ['block.timestamp', 'now']
        
        # Safe patterns (long time locks)
        self.safe_time_patterns = [
            r'(\d+)\s*(days|weeks|years)',  # Time units
            r'block\.timestamp\s*[+\-]\s*(\d{6,})',  # Large time buffers (> 100000 seconds ~= 27 hours)
        ]

    def enterContractDefinition(self, ctx):
        """Track current contract"""
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"

    def exitContractDefinition(self, ctx):
        """Reset contract context"""
        self.current_contract = None

    def enterFunctionDefinition(self, ctx):
        """Track current function"""
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.function_start_line = ctx.start.line
        
        # Check if function is view or pure
        function_text = ctx.getText()
        self.is_view_or_pure = 'view' in function_text or 'pure' in function_text

    def exitFunctionDefinition(self, ctx):
        """Reset function context"""
        self.in_function = False
        self.function_name = None
        self.is_view_or_pure = False

    def enterStatement(self, ctx):
        """Check statements for dangerous timestamp usage"""
        if not self.in_function or self.is_view_or_pure:
            return
        
        self.current_statement_line = ctx.start.line
        statement_text = ctx.getText()
        
        self._check_timestamp_usage(statement_text, ctx.start.line)

    def enterIfStatement(self, ctx):
        """Check if statements for timestamp comparisons"""
        if not self.in_function or self.is_view_or_pure:
            return
        
        statement_text = ctx.getText()
        self._check_timestamp_usage(statement_text, ctx.start.line)

    def _check_timestamp_usage(self, text, line):
        """Check if text contains dangerous timestamp usage"""
        text_lower = text.lower()
        
        # Check for timestamp sources
        timestamp_found = None
        for source in self.timestamp_sources:
            if source.lower() in text_lower:
                timestamp_found = source
                break
        
        if not timestamp_found:
            return
        
        # Check if it's a safe pattern (long time lock)
        if self._is_safe_time_pattern(text):
            return
        
        # Check if used in require/assert (critical checks)
        in_require_assert = 'require(' in text_lower or 'assert(' in text_lower
        
        # Check if used in comparison operators
        has_comparison = any(op in text for op in ['<', '>', '<=', '>=', '==', '!='])
        
        # Check if used in state-changing operations
        has_state_change = any(keyword in text_lower for keyword in [
            '=', 'transfer', 'send', 'call', 'delegatecall', 'selfdestruct'
        ])
        
        # Check if it's just for event emission or return value
        is_event_or_return = 'emit' in text_lower or text_lower.strip().startswith('return')
        
        if is_event_or_return:
            return
        
        # Report based on severity
        if in_require_assert and has_comparison:
            self.violations.append(
                f"⚠️  [S-SEC-015] WARNING: Dangerous timestamp usage in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                f"Using '{timestamp_found}' in require/assert statement. Miners can manipulate timestamps within ~15 seconds."
            )
        elif has_comparison and has_state_change:
            self.violations.append(
                f"⚠️  [S-SEC-015] WARNING: Timestamp-dependent state change in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                f"Using '{timestamp_found}' in conditional logic that affects state. Consider using block.number for short intervals."
            )

    def _is_safe_time_pattern(self, text):
        """Check if timestamp usage follows safe patterns (long time locks)"""
        # Check for time unit usage (days, weeks, years)
        for pattern in self.safe_time_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        # Check for large time buffers (> 1 hour = 3600 seconds)
        # Extract numbers near timestamp
        numbers = re.findall(r'\d+', text)
        for num in numbers:
            if int(num) >= 3600:  # At least 1 hour
                return True
        
        return False

    def get_violations(self):
        """Return all detected violations"""
        return self.violations
