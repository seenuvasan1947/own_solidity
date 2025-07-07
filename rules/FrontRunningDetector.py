from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class FrontRunningDetector(SolidityParserListener):
    def __init__(self):
        self.violations = []

    def enterFunctionDefinition(self, ctx):
        function_name = ctx.identifier().getText() if ctx.identifier() else None
        if function_name and ("getOrCreate" in function_name or "GetOrCreate" in function_name):
            # Check if the function is public or external
            visibility = None
            for i in range(ctx.getChildCount()):
                child = ctx.getChild(i)
                if isinstance(child, SolidityParser.VisibilityContext):
                    visibility = child.getText()
                    break

            if visibility in ["public", "external"]:
                line = ctx.start.line
                self.violations.append(f"❌ Potential front-running vulnerability in function '{function_name}' at line {line}: 'get-or-create' pattern detected. Consider separating creation and interaction or implementing protections.")

    def get_violations(self):
        return self.violations