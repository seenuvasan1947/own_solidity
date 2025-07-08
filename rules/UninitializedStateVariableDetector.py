from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class UninitializedStateVariableDetector(SolidityParserListener):
    """
    Detects state variables that are declared but not explicitly initialized.
    Uninitialized state variables rely on default values, which can lead to
    misunderstandings or subtle bugs if not explicitly intended.
    """
    def __init__(self):
        self.violations = []

    def enterStateVariableDeclaration(self, ctx: SolidityParser.StateVariableDeclarationContext):
        """
        Called when the parser enters a stateVariableDeclaration rule.
        Checks if the state variable has an initial value assigned (`Assign expression`).
        """
        # The 'stateVariableDeclaration' rule in the grammar is:
        # stateVariableDeclaration : type = typeName ... name = identifier (Assign initialValue = expression)? Semicolon;
        # We check if the 'initialValue' context is None, which means the (Assign initialValue = expression)? part was not present.
        if ctx.initialValue is None:
            variable_name = ctx.name.text if ctx.name else "unknown_variable"
            line = ctx.start.line
            self.violations.append(
                f"❌ Uninitialized state variable '{variable_name}' at line {line}: "
                "State variables should be explicitly initialized to prevent relying on default values implicitly."
            )

    def get_violations(self):
        """
        Returns the list of detected uninitialized state variable violations.
        """
        return self.violations