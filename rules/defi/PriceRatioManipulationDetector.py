from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class PriceRatioManipulationDetector(SolidityParserListener):
    def __init__(self):
        self.violations = []

    def enterFunctionCall(self, ctx):
        # Simplified detection: Look for calls to functions like `getPrice`, `getSpotPrice`, or similar
        # within public/external functions without additional protection like TWAP.
        func_name = ctx.expression().getText().lower()
        if any(keyword in func_name for keyword in ["getprice", "getspotprice", "price"]) and \
           any(token.text in ["public", "external"] for token in ctx.parser.getTokenStream().getTokens()):
            line = ctx.start.line
            self.violations.append(f"❌ Potentially vulnerable price calculation at line {line}: Price derived directly from DEX liquidity pool (spot price). Consider using TWAP or oracles.")

    def get_violations(self):
        return self.violations