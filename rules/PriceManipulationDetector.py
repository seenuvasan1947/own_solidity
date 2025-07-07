from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class PriceManipulationDetector(SolidityParserListener):
    def __init__(self):
        self.violations = []

    def enterFunctionCall(self, ctx):
        # Check if the function call involves DEX liquidity pool spot price
        text = ctx.getText().lower()
        if ("uniswap" in text or "pancakeswap" in text or "sushiswap" in text) and ("getreserves()" in text or "getamountsout" in text or "getamountin" in text):
            line = ctx.start.line
            self.violations.append(f"❌ Price calculated from DEX liquidity pool spot price at line {line}: {ctx.getText()}")

    def get_violations(self):
        return self.violations