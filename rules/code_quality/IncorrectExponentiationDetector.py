# S-CODE-011: Incorrect Exponentiation Operator Detection
# Detects usage of bitwise XOR (^) when exponentiation (**) was likely intended
# This is a common mistake that leads to incorrect calculations

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class IncorrectExponentiationDetector(SolidityParserListener):
    """
    Detects incorrect usage of ^ (XOR) operator when ** (exponentiation) was likely intended.
    
    This detector identifies:
    1. XOR operations with constant numbers (not hex)
    2. Patterns like 2^256, 10^18 that should be 2**256, 10**18
    3. XOR with powers of 10 or 2
    
    False Positive Mitigation:
    - Ignores XOR with hexadecimal values (0x...) - likely intentional bitwise ops
    - Ignores XOR in bitwise operation contexts
    - Only flags XOR with decimal constants that look like exponents
    - Checks for common exponentiation patterns (powers of 2, 10)
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None
        self.function_start_line = None
        
        # Common bases for exponentiation
        self.common_bases = ['2', '10', '16', '8']
        
        # Common exponents
        self.common_exponents = [
            '8', '16', '18', '32', '64', '128', '256',  # Powers of 2 and token decimals
            '3', '6', '9', '12', '15',  # Other common exponents
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

    def exitFunctionDefinition(self, ctx):
        """Reset function context"""
        self.in_function = False
        self.function_name = None

    def enterVariableDeclaration(self, ctx):
        """Check variable declarations for incorrect exponentiation"""
        var_text = ctx.getText()
        self._check_xor_pattern(var_text, ctx.start.line)

    def enterVariableDeclarationStatement(self, ctx):
        """Check variable declaration statements"""
        var_text = ctx.getText()
        self._check_xor_pattern(var_text, ctx.start.line)

    def enterExpression(self, ctx):
        """Check expressions for XOR that should be exponentiation"""
        if not self.in_function:
            return
        
        expr_text = ctx.getText()
        self._check_xor_pattern(expr_text, ctx.start.line)

    def enterStatement(self, ctx):
        """Check statements for incorrect exponentiation"""
        if not self.in_function:
            return
        
        stmt_text = ctx.getText()
        self._check_xor_pattern(stmt_text, ctx.start.line)

    def _check_xor_pattern(self, text, line):
        """Check if text contains XOR that should be exponentiation"""
        # Skip if no XOR operator
        if '^' not in text:
            return
        
        # Skip if contains ** (already using exponentiation)
        if '**' in text:
            return
        
        # Find all XOR patterns: number ^ number
        # Pattern: digit(s) ^ digit(s)
        xor_patterns = re.finditer(r'(\d+)\s*\^\s*(\d+)', text)
        
        for match in xor_patterns:
            base = match.group(1)
            exponent = match.group(2)
            full_match = match.group(0)
            
            # Check if either operand starts with 0x (hexadecimal)
            # If so, this is likely intentional bitwise XOR
            if '0x' in text[max(0, match.start()-2):match.end()+2].lower():
                continue
            
            # Check if this looks like exponentiation
            is_likely_exponentiation = False
            
            # Check 1: Common base and exponent combinations
            if base in self.common_bases and exponent in self.common_exponents:
                is_likely_exponentiation = True
            
            # Check 2: Base of 2 with any reasonable exponent
            if base == '2' and int(exponent) <= 256:
                is_likely_exponentiation = True
            
            # Check 3: Base of 10 with common decimal exponents
            if base == '10' and int(exponent) in [3, 6, 9, 12, 15, 18]:
                is_likely_exponentiation = True
            
            # Check 4: Pattern like "2^256 - 1" (max uint)
            if base == '2' and exponent == '256' and '-' in text:
                is_likely_exponentiation = True
            
            # Check 5: Large exponents (> 10) are rarely used in XOR
            if int(exponent) > 10:
                is_likely_exponentiation = True
            
            # Check 6: Context clues - variable names suggesting max values or decimals
            context_clues = ['max', 'decimal', 'unit', 'wei', 'ether', 'token']
            if any(clue in text.lower() for clue in context_clues):
                is_likely_exponentiation = True
            
            if is_likely_exponentiation:
                # Calculate what the values would be
                try:
                    xor_result = int(base) ^ int(exponent)
                    exp_result = int(base) ** int(exponent)
                    
                    # Only report if results are significantly different
                    if xor_result != exp_result:
                        self.violations.append(
                            f"❌ [S-CODE-011] CRITICAL: Incorrect exponentiation operator in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                            f"Using '{full_match}' (XOR) instead of '{base}**{exponent}' (exponentiation). "
                            f"Current result: {xor_result}, Expected result: {exp_result if exp_result < 10**20 else 'very large number'}. "
                            f"Use '**' operator for exponentiation, not '^' (XOR)."
                        )
                except (ValueError, OverflowError):
                    # If calculation fails, still report the issue
                    self.violations.append(
                        f"❌ [S-CODE-011] CRITICAL: Incorrect exponentiation operator in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                        f"Using '{full_match}' (XOR) instead of '{base}**{exponent}' (exponentiation). "
                        f"Use '**' operator for exponentiation, not '^' (XOR)."
                    )

    def get_violations(self):
        """Return all detected violations"""
        return self.violations
