from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class StaleValueDetector(SolidityParserListener):
    def __init__(self):
        self.violations = []
        self.in_view_function = False
        self.function_name = None
        self.state_variables = set()
        self.external_calls = []

    def enterContractDefinition(self, ctx):
        self.state_variables = set()
        self.external_calls = []

    def enterStateVariableDeclaration(self, ctx):
        name = ctx.name.getText()
        self.state_variables.add(name)

    def enterFunctionDefinition(self, ctx):
        self.in_view_function = False
        self.function_name = ctx.identifier().getText() if ctx.identifier() else None  # Handling for fallback/receive
        for i in range(ctx.getChildCount()):
            child = ctx.getChild(i)
            if child.getText() == 'view':
                self.in_view_function = True
                break
            elif child.getText() == 'pure': #pure functions can also return stale value
                self.in_view_function = True
                break

    def exitFunctionDefinition(self, ctx):
        if self.in_view_function:
            if self.external_calls: # if external call is present then, a state varible can be potentially stale
                line = ctx.start.line
                reason = f"❌ View/Pure function '{self.function_name}' at line {line} might return a stale value due to external calls."
                self.violations.append(reason)
        self.in_view_function = False
        self.function_name = None
        self.external_calls = []

    def enterFunctionCall(self, ctx):
        if self.in_view_function:
            # Basic check for external calls (more sophisticated analysis might be needed)
            identifier_path = ctx.expression().getText()
            if "." in identifier_path:
                self.external_calls.append(identifier_path)

    def get_violations(self):
        return self.violations