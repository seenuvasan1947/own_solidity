# S-CODE-031: Incorrect Unary Expression
# Detects dangerous unary expressions like =+ instead of +=
# Common typo that causes logic errors

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class IncorrectUnaryDetector(SolidityParserListener):
    
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

    def enterStateVariableDeclaration(self, ctx):
        var_text = ctx.getText()
        line = ctx.start.line
        
        # Detect =+ pattern in state variable initialization
        if re.search(r'=\s*\+\s*\d', var_text):
            self.violations.append(
                f"⚠️  [S-CODE-031] LOW: Dangerous unary expression in state variable of contract '{self.current_contract}' at line {line}: "
                f"Pattern '=+' detected. Did you mean '+='? "
                f"Fix the operator."
            )

    def enterStatement(self, ctx):
        if not self.in_function:
            return
        
        stmt_text = ctx.getText()
        line = ctx.start.line
        
        # Detect =+ pattern (assignment with unary plus)
        # Pattern: variable = +number
        if re.search(r'=\s*\+\s*\d', stmt_text):
            # Avoid FP: skip if it's actually += split across formatting
            if '+=' not in stmt_text:
                self.violations.append(
                    f"⚠️  [S-CODE-031] LOW: Dangerous unary expression in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                    f"Pattern '=+' detected. Did you mean '+='? "
                    f"This will assign the positive value instead of incrementing."
                )

    def get_violations(self):
        return self.violations
