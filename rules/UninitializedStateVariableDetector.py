from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class UninitializedStateVariableDetector(SolidityParserListener):
    def __init__(self):
        self.violations = []

    def enterStateVariableDeclaration(self, ctx: SolidityParser.StateVariableDeclarationContext):
        # A state variable is uninitialized if the 'initialValue' expression is missing.
        # The grammar rule is: (Assign initialValue = expression)?
        # If 'initialValue' is None, it means there was no assignment at declaration.
        if ctx.initialValue is None:
            variable_name = ctx.name.getText()
            line = ctx.start.line
            self.violations.append(
                f"❌ Uninitialized state variable '{variable_name}' at line {line}: "
                "State variables should be explicitly initialized to prevent critical issues "
                "from default zero values."
            )

    def get_violations(self):
        return self.violations