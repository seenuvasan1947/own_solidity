from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class StaleValueDetector(SolidityParserListener):
    def __init__(self):
        self.in_view_function = False
        self.function_name = ""
        self.violations = []

    def enterFunctionDefinition(self, ctx):
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "fallback/receive"  # Handle fallback/receive functions

        # Check for 'view' stateMutability
        for i in range(ctx.getChildCount()):
            if ctx.getChild(i).getText() == "view":
                self.in_view_function = True
                break

    def exitFunctionDefinition(self, ctx):
        self.in_view_function = False
        self.function_name = ""

    def enterFunctionCall(self, ctx):
        if self.in_view_function:
            # This is a simplified check.  A real-world detector would need to
            # analyze the called function to see if it *could* modify state
            # indirectly (e.g., calling another contract).
            function_call_text = ctx.getText().lower()
            if "call" in function_call_text or "delegatecall" in function_call_text or "staticcall" in function_call_text or "send" in function_call_text or "transfer" in function_call_text:
                line = ctx.start.line
                self.violations.append(f"❌ Potential stale value returned by view function '{self.function_name}' at line {line}: Function call '{ctx.getText()}' might lead to inconsistent state being read.")


    def get_violations(self):
        return self.violations