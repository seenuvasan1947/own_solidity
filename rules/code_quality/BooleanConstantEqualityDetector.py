# S-CODE-022: Boolean Constant Equality
# Detects comparisons to boolean constants (== true, == false)
# Redundant and reduces code readability

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class BooleanConstantEqualityDetector(SolidityParserListener):
    
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
        
        # Detect comparisons to boolean constants
        patterns = [
            r'==\s*true\b',
            r'\btrue\s*==',
            r'==\s*false\b',
            r'\bfalse\s*==',
            r'!=\s*true\b',
            r'\btrue\s*!=',
            r'!=\s*false\b',
            r'\bfalse\s*!=',
        ]
        
        for pattern in patterns:
            if re.search(pattern, stmt_text):
                self.violations.append(
                    f"ℹ️  [S-CODE-022] INFO: Boolean constant comparison in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                    f"Comparing to boolean constant is redundant. "
                    f"Use the boolean variable directly or with ! operator."
                )
                break

    def get_violations(self):
        return self.violations
