from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class StateVariableInitializationDetector(SolidityParserListener):
    def __init__(self):
        self.violations = []

    def enterStateVariableDeclaration(self, ctx):
        # Check if state variable is initialized
        if ctx.assign() is None and ctx.getChild(0).getText() not in ['constant', 'immutable']:
            line = ctx.start.line
            self.violations.append(f"❌ Uninitialized state variable at line {line}: {ctx.getText()}")

    def get_violations(self):
        return self.violations