from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class UninitializedStateVariableDetector(SolidityParserListener):
    def __init__(self):
        self.violations = []

    def enterStateVariableDeclaration(self, ctx: SolidityParser.StateVariableDeclarationContext):
        # Check if an initial value is assigned
        if ctx.initialValue() is None:
            variable_name = ctx.name.text
            line = ctx.start.line
            self.violations.append(
                f"❌ Uninitialized State Variable at line {line}: State variable '{variable_name}' is not explicitly initialized."
            )

    def get_violations(self):
        return self.violations