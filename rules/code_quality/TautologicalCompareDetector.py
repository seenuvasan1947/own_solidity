# S-CODE-028: Tautological Compare
# Detects comparisons of a variable to itself
# Always returns true or false, indicating logic error

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class TautologicalCompareDetector(SolidityParserListener):
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"

    def exitContractDefinition(self, ctx):
        self.current_contract = None

    def enterFunctionDefinition(self, ctx):
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"

    def exitFunctionDefinition(self, ctx):
        self.in_function = False
        self.function_name = None

    def enterStatement(self, ctx):
        if not self.in_function:
            return
        
        stmt_text = ctx.getText()
        line = ctx.start.line
        
        # Detect self-comparisons: a == a, a >= a, a <= a, a > a, a < a, a != a
        # Pattern: variable operator variable (same variable)
        patterns = [
            (r'(\w+)\s*==\s*\1\b', '=='),
            (r'(\w+)\s*>=\s*\1\b', '>='),
            (r'(\w+)\s*<=\s*\1\b', '<='),
            (r'(\w+)\s*>\s*\1\b', '>'),
            (r'(\w+)\s*<\s*\1\b', '<'),
            (r'(\w+)\s*!=\s*\1\b', '!='),
        ]
        
        for pattern, op in patterns:
            match = re.search(pattern, stmt_text)
            if match:
                var_name = match.group(1)
                # Skip common false positives like type names
                if var_name not in ['uint', 'uint256', 'int', 'address', 'bool', 'bytes']:
                    self.violations.append(
                        f"⚠️  [S-CODE-028] MEDIUM: Tautological comparison in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                        f"Variable '{var_name}' compared to itself using '{op}'. "
                        f"This always returns the same result. Check for copy-paste error."
                    )
                    break

    def get_violations(self):
        return self.violations
