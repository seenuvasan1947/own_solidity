from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class PriceRatioManipulationDetector(SolidityParserListener):
    def __init__(self):
        self.violations = []
        self.in_function = False

    def enterFunctionDefinition(self, ctx):
        self.in_function = True

    def exitFunctionDefinition(self, ctx):
        self.in_function = False

    def enterFunctionCall(self, ctx):
        if not self.in_function:
            return
        function_name = ctx.expression().getText()
        if "getReserves" in function_name or "getPrice" in function_name:
            line = ctx.start.line
            self.violations.append(f"❌ Vulnerable price calculation at line {line}: Price derived directly from DEX liquidity pool via {function_name}.")

    def get_violations(self):
        return self.violations