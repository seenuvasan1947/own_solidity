from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class PriceRatioManipulationDetector(SolidityParserListener):
    def __init__(self):
        self.violations = []

    def enterFunctionCall(self, ctx):
        # Detect patterns like: `token0.balance() / token1.balance()`
        try:
            if ctx.identifier().getText() in ["getPrice","getSpotPrice", "calculatePrice","get_price"]:
                if "balance" in ctx.getText() and "/" in ctx.getText():
                    line = ctx.start.line
                    self.violations.append(f"❌ Price calculated by ratio of token balances at line {line}: {ctx.getText()}")
        except:
            pass


    def get_violations(self):
        return self.violations