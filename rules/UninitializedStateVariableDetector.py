from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class UninitializedStateVariableDetector(SolidityParserListener):
    def __init__(self):
        self.violations = []

    def enterStateVariableDeclaration(self, ctx: SolidityParser.StateVariableDeclarationContext):
        # A state variable declaration is considered uninitialized if the 'initialValue' context is None.
        # This checks for the absence of the ' = expression' part in the declaration.
        if ctx.initialValue is None:
            variable_name = ctx.name.text
            line = ctx.start.line
            self.violations.append(
                f"❌ Uninitialized state variable '{variable_name}' at line {line}: "
                f"State variable is declared but not explicitly initialized. "
                f"It will be initialized to its default value (e.g., 0 for integers, address(0) for addresses, empty for strings, etc.). "
                f"Consider explicit initialization for clarity and security."
            )

    def get_violations(self):
        return self.violations