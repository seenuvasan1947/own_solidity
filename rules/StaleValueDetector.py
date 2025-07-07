from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class StaleValueDetector(SolidityParserListener):
    def __init__(self):
        self.violations = []
        self.current_function_name = None
        self.is_view_function = False
        self.external_call_present = False

    def enterFunctionDefinition(self, ctx):
        self.current_function_name = ctx.identifier().getText() if ctx.identifier() else "fallback/receive" # Handles fallback/receive cases
        self.is_view_function = False
        self.external_call_present = False

        # Check for view or pure state mutability
        for i in range(ctx.getChildCount()):
            if ctx.getChild(i).getText() in ["view", "pure"]:
                self.is_view_function = True
                break


    def exitFunctionDefinition(self, ctx):
        if self.is_view_function and self.external_call_present:
            line = ctx.start.line
            self.violations.append(f"❌ SOL-AM-DA-1: Stale value risk in view function '{self.current_function_name}' at line {line}. It contains external calls and may return inconsistent data.")

        self.current_function_name = None
        self.is_view_function = False
        self.external_call_present = False


    def enterFunctionCall(self, ctx):
        # Check for external function calls
        try:
            # basic check
            potential_identifier_path = ctx.expression().getText()
            if "(" not in potential_identifier_path:
               return


            first_node = ctx.expression().getChild(0)

            if isinstance(first_node, SolidityParser.IdentifierContext):
                 self.external_call_present = True  # Mark external call

            elif isinstance(first_node, SolidityParser.MemberAccessContext):

                self.external_call_present = True
        except:
            pass


    def get_violations(self):
        return self.violations