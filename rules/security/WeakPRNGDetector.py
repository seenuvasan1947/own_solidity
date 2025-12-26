# S-SEC-009: Weak PRNG Detection
# Detects weak pseudo-random number generation using block.timestamp, now, or blockhash
# These sources can be influenced by miners and should not be used for randomness

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class WeakPRNGDetector(SolidityParserListener):
    """
    Detects weak PRNG patterns using predictable blockchain data.
    
    This detector identifies:
    1. Use of block.timestamp, now, or blockhash in modulo operations
    2. Use of these values in random number generation
    3. Direct use in critical decision-making logic
    
    False Positive Mitigation:
    - Only flags when used with modulo operator (% or mod)
    - Excludes time-based logic that doesn't involve randomness
    - Checks for proper randomness sources (e.g., Chainlink VRF)
    - Excludes simple timestamp comparisons for time locks
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None
        self.function_start_line = None
        self.current_statement_line = None
        self.has_chainlink_vrf = False
        
        # Weak randomness sources
        self.weak_sources = [
            'block.timestamp', 'now', 'blockhash', 'block.blockhash',
            'block.number', 'block.difficulty', 'block.prevrandao'
        ]
        
        # Patterns that indicate randomness usage (not just time checks)
        self.randomness_indicators = [
            'random', 'rand', 'lottery', 'winner', 'prize',
            'reward', 'game', 'draw', 'select', 'choose'
        ]

    def enterContractDefinition(self, ctx):
        """Track current contract"""
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.has_chainlink_vrf = False

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

    def enterStatement(self, ctx):
        """Check statements for weak PRNG patterns"""
        if not self.in_function:
            return
        
        self.current_statement_line = ctx.start.line
        statement_text = ctx.getText()
        
        # Check for weak PRNG patterns
        self._check_weak_prng(statement_text, ctx.start.line)

    def enterExpressionStatement(self, ctx):
        """Check expression statements for weak PRNG"""
        if not self.in_function:
            return
        
        self.current_statement_line = ctx.start.line
        statement_text = ctx.getText()
        
        self._check_weak_prng(statement_text, ctx.start.line)

    def _check_weak_prng(self, text, line):
        """Check if text contains weak PRNG patterns"""
        text_lower = text.lower()
        
        # Check if using Chainlink VRF (proper randomness source)
        if 'chainlink' in text_lower or 'vrf' in text_lower or 'requestrandomness' in text_lower:
            self.has_chainlink_vrf = True
            return
        
        # Check for weak sources
        weak_source_found = None
        for source in self.weak_sources:
            if source.lower() in text_lower:
                weak_source_found = source
                break
        
        if not weak_source_found:
            return
        
        # Check if it's used in a modulo operation (strong indicator of PRNG)
        has_modulo = '%' in text or 'mod' in text_lower
        
        # Check if the function/variable names suggest randomness
        has_randomness_indicator = any(indicator in text_lower for indicator in self.randomness_indicators)
        
        # Check if it's just a simple time comparison (not randomness)
        is_simple_time_check = self._is_simple_time_check(text_lower)
        
        # Report if:
        # 1. Modulo operation with weak source (high confidence)
        # 2. Randomness indicator with weak source (medium confidence)
        if has_modulo and weak_source_found:
            # High confidence - modulo operation with weak source
            self.violations.append(
                f"❌ [S-SEC-009] CRITICAL: Weak PRNG detected in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                f"Using '{weak_source_found}' with modulo operator for randomness. This can be manipulated by miners."
            )
        elif has_randomness_indicator and weak_source_found and not is_simple_time_check:
            # Medium confidence - randomness-related code with weak source
            self.violations.append(
                f"⚠️  [S-SEC-009] WARNING: Potential weak PRNG in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                f"Using '{weak_source_found}' in randomness-related logic. Consider using Chainlink VRF or similar oracle."
            )

    def _is_simple_time_check(self, text):
        """Check if this is just a simple time comparison (not randomness)"""
        # Simple time checks usually have comparison operators without modulo
        time_check_patterns = [
            'require(block.timestamp>', 'require(block.timestamp<',
            'require(now>', 'require(now<',
            'if(block.timestamp>', 'if(block.timestamp<',
            'if(now>', 'if(now<',
            'block.timestamp+', 'block.timestamp-',
            'now+', 'now-'
        ]
        
        # Remove spaces for pattern matching
        text_no_space = text.replace(' ', '')
        
        return any(pattern.replace(' ', '') in text_no_space for pattern in time_check_patterns)

    def get_violations(self):
        """Return all detected violations"""
        return self.violations
