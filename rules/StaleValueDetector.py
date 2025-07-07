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
        name = ctx.identifier().getText()
        self.state_variables.add(name)

    def enterFunctionDefinition(self, ctx):
        self.current_function_name = ctx.identifier().getText()
        self.is_view_function = False
        for modifier in ctx.getChildren():
            if isinstance(modifier, SolidityParser.VisibilityContext):
                continue # Visibility doesn't define if it's view
            if isinstance(modifier, SolidityParser.StateMutabilityContext):
                if modifier.getText() == "view":
                    self.is_view_function = True
                    break

    def exitFunctionDefinition(self, ctx):
        self.current_function_name = None
        self.is_view_function = False

    def enterExpression(self, ctx:SolidityParser.ExpressionContext):

        if self.is_view_function:
            # check if state variable is accessed inside view function
            try:
                if ctx.identifier() is not None:
                    name = ctx.identifier().getText()
                    if name in self.state_variables:
                        line = ctx.start.line
                        self.violations.append(f"❌ Potential stale value read in view function '{self.current_function_name}' at line {line}: Accesses state variable '{name}'. Consider reentrancy implications.")
            except:
                pass

    def get_violations(self):
        return self.violations