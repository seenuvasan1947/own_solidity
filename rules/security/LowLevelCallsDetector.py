# S-SEC-017: Low-Level Calls Detection
# Detects usage of low-level calls (.call, .delegatecall, .staticcall)
# Low-level calls are error-prone and don't check for code existence

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class LowLevelCallsDetector(SolidityParserListener):
    """
    Detects usage of low-level calls which are error-prone.
    
    This detector identifies:
    1. .call() usage
    2. .delegatecall() usage
    3. .staticcall() usage
    4. .callcode() usage (deprecated)
    
    False Positive Mitigation:
    - Provides informational warnings, not errors
    - Distinguishes between checked and unchecked calls
    - Excludes calls with proper return value checking
    - Notes if call is in try-catch block
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None
        self.function_start_line = None
        self.in_try_catch = False
        
        # Low-level call patterns
        self.low_level_calls = ['.call', '.delegatecall', '.staticcall', '.callcode']

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

    def exitFunctionDefinition(self, ctx):
        """Reset function context"""
        self.in_function = False
        self.function_name = None

    def enterTryStatement(self, ctx):
        """Track try-catch blocks"""
        self.in_try_catch = True

    def exitTryStatement(self, ctx):
        """Exit try-catch block"""
        self.in_try_catch = False

    def enterExpression(self, ctx):
        """Check expressions for low-level calls"""
        if not self.in_function:
            return
        
        expr_text = ctx.getText()
        self._check_low_level_call(expr_text, ctx.start.line)

    def enterStatement(self, ctx):
        """Check statements for low-level calls"""
        if not self.in_function:
            return
        
        stmt_text = ctx.getText()
        self._check_low_level_call(stmt_text, ctx.start.line)

    def _check_low_level_call(self, text, line):
        """Check if text contains low-level calls"""
        text_lower = text.lower()
        
        # Find low-level calls
        for call_type in self.low_level_calls:
            if call_type in text_lower:
                # Check if return value is checked
                has_return_check = self._has_return_value_check(text)
                
                # Check if deprecated callcode
                is_deprecated = '.callcode' in text_lower
                
                # Determine severity
                if is_deprecated:
                    severity = "WARNING"
                    symbol = "⚠️ "
                    message = f"Deprecated low-level call {call_type}() in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: " \
                             f"callcode is deprecated. Use delegatecall instead."
                elif not has_return_check and not self.in_try_catch:
                    severity = "WARNING"
                    symbol = "⚠️ "
                    message = f"Unchecked low-level call {call_type}() in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: " \
                             f"Return value is not checked. Ensure the call success is verified or failures are logged."
                else:
                    severity = "INFO"
                    symbol = "ℹ️  "
                    message = f"Low-level call {call_type}() in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: " \
                             f"Low-level calls are error-prone. Consider using higher-level abstractions when possible."
                
                self.violations.append(f"{symbol} [S-SEC-017] {severity}: {message}")
                break  # Only report once per statement

    def _has_return_value_check(self, text):
        """Check if the low-level call's return value is checked"""
        # Pattern: (bool success, ) = addr.call(...)
        # Pattern: bool success = addr.call(...)
        # Pattern: require(addr.call(...))
        # Pattern: if (addr.call(...))
        
        return_check_patterns = [
            r'bool\s+\w+\s*=',  # bool success =
            r'\(bool\s+\w+',     # (bool success, ...)
            r'require\s*\(',     # require(call)
            r'if\s*\(',          # if (call)
            r'assert\s*\(',      # assert(call)
        ]
        
        for pattern in return_check_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False

    def get_violations(self):
        """Return all detected violations"""
        return self.violations
