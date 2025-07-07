from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class StaleValueDetector(SolidityParserListener):
    def __init__(self):
        self.violations = []
        self.current_function_name = None
        self.is_view_function = False
        self.state_variables = set()

    def enterStateVariableDeclaration(self, ctx):
        """Collect state variables."""
        name_ctx = ctx.identifier()
        if name_ctx:
            self.state_variables.add(name_ctx.getText())


    def enterFunctionDefinition(self, ctx):
        """Check if function is a view function."""
        self.current_function_name = ctx.identifier().getText() if ctx.identifier() else None
        self.is_view_function = False

        for modifier in ctx.getChildren():
            if modifier.getText() == "view":
                self.is_view_function = True
                break

    def exitFunctionDefinition(self, ctx):
        """Reset function context."""
        self.current_function_name = None
        self.is_view_function = False

    def enterIdentifier(self, ctx):
        """Check for state variable access within view functions."""
        if self.is_view_function and ctx.getText() in self.state_variables:
            line = ctx.start.line
            self.violations.append(f"❌ Potential stale value in view function '{self.current_function_name}' at line {line}: Access to state variable '{ctx.getText()}' during potential reentrancy.")


    def get_violations(self):
        return self.violations