from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class PriceManipulationDetector(SolidityParserListener):
    def __init__(self):
        self.violations = []

    def enterFunctionCall(self, ctx):
        func_name = ctx.expression().getText()

        # Check for direct DEX price usage.  This is a simplified example.  A real-world
        # detector would need much more sophisticated analysis to identify DEX pool reads.
        if "get_price" in func_name.lower() or "getPrice" in func_name or "currentPrice" in func_name or "getSpotPrice" in func_name or  "spotPrice" in func_name : # very basic check
            line = ctx.start.line
            self.violations.append(f"❌ Potential price manipulation vulnerability at line {line}: Direct DEX price usage detected in function call: {func_name}. Consider using TWAP or an oracle.")

    def get_violations(self):
        return self.violations