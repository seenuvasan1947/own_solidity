from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class UninitializedStateVariableDetector(SolidityParserListener):
    def __init__(self):
        self.violations = []

    def enterStateVariableDeclaration(self, ctx: SolidityParser.StateVariableDeclarationContext):
        # Check if the state variable is explicitly initialized.
        # ctx.initialValue() returns the 'expression' context if an initial value is assigned, None otherwise.
        if ctx.initialValue() is None:
            is_constant = False
            is_immutable = False
            
            # Check for 'Constant' and 'Immutable' modifiers.
            # We iterate through the children of the stateVariableDeclaration context
            # to find the specific terminal nodes representing these keywords.
            for child in ctx.children:
                if isinstance(child, TerminalNode):
                    if child.getSymbol().type == SolidityLexer.Constant:
                        is_constant = True
                        break # 'constant' variables must be initialized by compiler rules, so we don't flag them here.
                    if child.getSymbol().type == SolidityLexer.Immutable:
                        is_immutable = True
                        # Do not break here, continue to check for other modifiers if necessary,
                        # though for this rule, we only care about constant/immutable.
            
            # A violation is reported if:
            # 1. The variable lacks an explicit initialization at its declaration point.
            # 2. It is NOT a 'constant' variable (compiler handles this).
            # 3. It is NOT an 'immutable' variable (these can be validly initialized in the constructor).
            # The rule targets regular state variables that default to zero values, which can be an oversight.
            if not is_constant and not is_immutable:
                line = ctx.start.line
                variable_name = ctx.name.getText() # Get the name of the variable
                self.violations.append(
                    f"❌ Uninitialized state variable '{variable_name}' at line {line}: "
                    "Important state variables should be explicitly initialized to prevent unexpected default values, "
                    "enhancing clarity and preventing subtle bugs."
                )

    def get_violations(self):
        return self.violations