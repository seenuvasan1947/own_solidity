from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class UninitializedStateVariableDetector(SolidityParserListener):
    def __init__(self):
        self.violations = []

    def enterStateVariableDeclaration(self, ctx: SolidityParser.StateVariableDeclarationContext):
        """
        Detects uninitialized state variables that are not explicitly marked as constant or immutable.
        """
        # Check if an assignment operator is present (meaning it's initialized)
        is_initialized = ctx.Assign() is not None

        # Check if the variable is marked 'constant'
        is_constant = ctx.Constant() is not None

        # Check if the variable is marked 'immutable'
        is_immutable = ctx.Immutable() is not None

        # If it's not initialized AND not constant AND not immutable, it's a potential issue.
        # Constant variables MUST be initialized at declaration by the compiler, so this
        # condition handles regular mutable state variables. Immutable variables can be
        # initialized in the constructor, so not initializing them at declaration isn't
        # necessarily a bug, but leaving regular state variables uninitialized relies on
        # default values which might be unexpected or insecure.
        if not is_initialized and not is_constant and not is_immutable:
            variable_name = ctx.identifier().getText()
            line = ctx.start.line
            reason = f"State variable '{variable_name}' at line {line} is declared but not explicitly initialized. It will be initialized with its default value (e.g., 0 for uint, false for bool, address(0) for address), which might not be the intended secure state."
            self.violations.append(reason)

    def get_violations(self):
        return self.violations