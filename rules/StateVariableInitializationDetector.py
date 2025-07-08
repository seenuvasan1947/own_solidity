from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class StateVariableInitializationDetector(SolidityParserListener):
    def __init__(self):
        self.violations = []

    def enterStateVariableDeclaration(self, ctx):
        # Check if state variable is initialized
        if ctx.initialValue() is None:
            line = ctx.start.line
            variable_name = ctx.name.getText()
            self.violations.append(f"❌ Uninitialized state variable '{variable_name}' at line {line}: State variables should be explicitly initialized.")

    def get_violations(self):
        return self.violations