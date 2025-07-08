from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class UninitializedStateVariableDetector(SolidityParserListener):
    def __init__(self):
        self.violations = []

    def enterStateVariableDeclaration(self, ctx: SolidityParser.StateVariableDeclarationContext):
        # A state variable declaration without an initial value assigned.
        # Example: uint256 myVariable;
        if ctx.initialValue is None:
            line = ctx.start.line
            variable_name = ctx.name.getText()
            full_declaration = ctx.getText()
            self.violations.append(
                f"⚠️ Uninitialized state variable '{variable_name}' at line {line}: '{full_declaration}'. "
                "Explicitly initializing state variables is a best practice to avoid unexpected default values."
            )

    def get_violations(self):
        return self.violations