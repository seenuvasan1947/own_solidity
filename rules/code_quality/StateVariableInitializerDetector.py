from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class StateVariableInitializerDetector(SolidityParserListener):
    def __init__(self):
        self.violations = []

    def enterStateVariableDeclaration(self, ctx):
        # Check if the state variable has an explicit initialization
        if ctx.Assign() is None:
            line = ctx.start.line
            var_name = ctx.name.getText()
            self.violations.append(f"❌ Uninitialized state variable '{var_name}' at line {line}: Explicit initialization is required.")

    def get_violations(self):
        return self.violations