# S-CODE-025: Divide Before Multiply
# Detects division before multiplication which causes precision loss
# Integer division truncates, leading to incorrect calculations

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class DivideBeforeMultiplyDetector(SolidityParserListener):
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None
        self.function_body = []
        self.division_vars = {}  # {var_name: line}

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"

    def exitContractDefinition(self, ctx):
        self.current_contract = None

    def enterFunctionDefinition(self, ctx):
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.function_body = []
        self.division_vars = {}

    def exitFunctionDefinition(self, ctx):
        self.in_function = False
        self.function_name = None

    def enterStatement(self, ctx):
        if not self.in_function:
            return
        
        stmt_text = ctx.getText()
        line = ctx.start.line
        self.function_body.append((line, stmt_text))
        
        # Track division results
        div_match = re.search(r'(\w+)\s*=.*/', stmt_text)
        if div_match and '==' not in stmt_text:  # Exclude equality checks
            var_name = div_match.group(1)
            self.division_vars[var_name] = line
        
        # Check if division result is multiplied
        for var_name, div_line in list(self.division_vars.items()):
            if var_name in stmt_text and '*' in stmt_text and line > div_line:
                # Avoid FP: skip if in require/assert with equality
                if not (('require' in stmt_text or 'assert' in stmt_text) and '==' in stmt_text):
                    self.violations.append(
                        f"⚠️  [S-CODE-025] MEDIUM: Divide before multiply in function '{self.function_name}' of contract '{self.current_contract}': "
                        f"Variable '{var_name}' from division at line {div_line} is multiplied at line {line}. "
                        f"Integer division truncates. Consider multiplying before dividing for better precision."
                    )
                    # Remove to avoid duplicate reports
                    del self.division_vars[var_name]

    def get_violations(self):
        return self.violations
