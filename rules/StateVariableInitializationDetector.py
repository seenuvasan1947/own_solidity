from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class StateVariableInitializationDetector(SolidityParserListener):
    def __init__(self):
        self.state_variables = {}
        self.violations = []

    def enterStateVariableDeclaration(self, ctx):
        var_name = ctx.name.getText()
        if ctx.initialValue() is None:
            line = ctx.start.line
            self.violations.append(f"❌ Uninitialized state variable '{var_name}' at line {line}")

    def get_violations(self):
        return self.violations