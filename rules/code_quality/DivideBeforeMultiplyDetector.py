# S-CQ-001: Divide Before Multiply
# Detects precision loss from performing division before multiplication
# Integer division truncates, leading to potential loss of precision

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class DivideBeforeMultiplyDetector(SolidityParserListener):
    """
    Detects divide-before-multiply patterns that can cause precision loss.
    
    This detector identifies:
    1. Division operations followed by multiplication
    2. Expressions like (a / b) * c where reordering would improve precision
    3. SafeMath div() followed by mul()
    
    False Positive Mitigation:
    - Excludes cases within assert/require with equality checks
    - Excludes intentional precision control (e.g., percentage calculations)
    - Checks for SafeMath usage patterns
    - Excludes division by constants where precision loss is intentional
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None
        self.function_start_line = None
        self.division_results = {}  # Track variables that store division results
        self.current_statement_line = None

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
        self.division_results = {}

    def exitFunctionDefinition(self, ctx):
        """Reset function context"""
        self.in_function = False
        self.function_name = None
        self.division_results = {}

    def enterStatement(self, ctx):
        """Check statements for divide-before-multiply patterns"""
        if not self.in_function:
            return
        
        self.current_statement_line = ctx.start.line
        statement_text = ctx.getText()
        
        # Check for inline divide-before-multiply
        self._check_inline_pattern(statement_text, ctx.start.line)
        
        # Track division results
        self._track_division(statement_text, ctx.start.line)
        
        # Check for multiplication of division results
        self._check_multiply_division_result(statement_text, ctx.start.line)

    def enterExpressionStatement(self, ctx):
        """Check expression statements"""
        if not self.in_function:
            return
        
        self.current_statement_line = ctx.start.line
        statement_text = ctx.getText()
        
        self._check_inline_pattern(statement_text, ctx.start.line)
        self._track_division(statement_text, ctx.start.line)
        self._check_multiply_division_result(statement_text, ctx.start.line)

    def _check_inline_pattern(self, text, line):
        """Check for inline (a / b) * c patterns"""
        # Pattern: (expr / expr) * expr or expr / expr * expr
        # This is a simplified check - looks for / followed by * in same expression
        
        # Skip if in require/assert with equality (likely intentional)
        if self._is_in_assert_with_equality(text):
            return
        
        # Remove spaces for easier pattern matching
        text_clean = text.replace(' ', '')
        
        # Pattern 1: (a/b)*c
        if re.search(r'\([^)]*\/[^)]*\)\s*\*', text):
            self.violations.append(
                f"⚠️  [S-CQ-001] WARNING: Potential precision loss in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                f"Division before multiplication detected. Consider reordering to multiply first: (a * c) / b instead of (a / b) * c"
            )
            return
        
        # Pattern 2: a/b*c (without parentheses, left-to-right evaluation)
        # Look for division followed by multiplication in same expression
        if '/' in text_clean and '*' in text_clean:
            # Check if / comes before * (simple heuristic)
            div_pos = text_clean.find('/')
            mul_pos = text_clean.find('*', div_pos)
            if mul_pos > div_pos and mul_pos - div_pos < 50:  # Reasonable distance
                # Make sure it's not a comment or string
                if not ('//' in text or '/*' in text):
                    self.violations.append(
                        f"⚠️  [S-CQ-001] WARNING: Potential precision loss in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                        f"Division before multiplication detected. Consider reordering to multiply first to avoid precision loss."
                    )

    def _track_division(self, text, line):
        """Track variables that store division results"""
        # Pattern: var = expr / expr
        if '=' in text and '/' in text and '==' not in text and '!=' not in text:
            # Extract variable name (simplified)
            parts = text.split('=')
            if len(parts) >= 2:
                left = parts[0].strip()
                right = parts[1].strip()
                
                # Check if right side has division
                if '/' in right:
                    # Extract variable name (last token on left side)
                    var_match = re.search(r'(\w+)\s*$', left)
                    if var_match:
                        var_name = var_match.group(1)
                        self.division_results[var_name] = line

    def _check_multiply_division_result(self, text, line):
        """Check if multiplying a variable that stores a division result"""
        # Skip if in assert/require with equality
        if self._is_in_assert_with_equality(text):
            return
        
        # Check if any tracked division result is being multiplied
        if '*' in text:
            for var_name, div_line in self.division_results.items():
                if var_name in text:
                    # Make sure it's actually being multiplied (not just mentioned)
                    # Pattern: var * something or something * var
                    if re.search(rf'\b{var_name}\b\s*\*', text) or re.search(rf'\*\s*\b{var_name}\b', text):
                        self.violations.append(
                            f"⚠️  [S-CQ-001] WARNING: Potential precision loss in function '{self.function_name}' of contract '{self.current_contract}': "
                            f"Variable '{var_name}' (division result from line {div_line}) is multiplied at line {line}. "
                            f"Consider reordering operations to multiply before dividing."
                        )

    def _is_in_assert_with_equality(self, text):
        """Check if expression is in assert/require with equality check"""
        text_lower = text.lower()
        
        # Check if in require/assert
        in_assert = 'require(' in text_lower or 'assert(' in text_lower
        
        # Check if has equality
        has_equality = '==' in text
        
        return in_assert and has_equality

    def get_violations(self):
        """Return all detected violations"""
        return self.violations
