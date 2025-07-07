from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class StaleValueDetector(SolidityParserListener):
    def __init__(self):
        self.violations = []
        self.current_function_name = None
        self.is_view_function = False

    def enterFunctionDefinition(self, ctx):
        self.current_function_name = ctx.identifier().getText() if ctx.identifier() else 'anonymous'
        self.is_view_function = False
        for modifier in ctx.getChildren():
            if modifier.getText() == 'view':
                self.is_view_function = True
                break

    def exitFunctionDefinition(self, ctx):
        self.current_function_name = None
        self.is_view_function = False

    def enterContractDefinition(self, ctx):
        self.contract_name = ctx.name.text

    def exitContractDefinition(self, ctx):
        self.contract_name = None


    def enterFunctionCall(self, ctx):
        if self.is_view_function:
            function_call_text = ctx.getText()
            # A more sophisticated check could involve looking at what the function call does
            # and whether it might lead to an inconsistent state.  For now, flag all external calls.
            if "(" in function_call_text and "." in function_call_text and not function_call_text.startswith(self.contract_name):
                line = ctx.start.line
                self.violations.append(f"❌ Potential stale value in view function '{self.current_function_name}' at line {line}: External function call '{function_call_text}' might return inconsistent data.")

    def get_violations(self):
        return self.violations


-