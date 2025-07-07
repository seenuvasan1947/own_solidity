from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class PriceRatioManipulationDetector(SolidityParserListener):
    def __init__(self):
        self.violations = []

    def enterFunctionCall(self, ctx):
        # This is a simplified check.  A more robust implementation would require data flow analysis.
        # Here, we look for a function call that looks like price = token0.balance() / token1.balance()
        text = ctx.getText()
        if "/" in text and ".balance()" in text:
            line = ctx.start.line
            self.violations.append(f"❌ Price calculated by ratio of token balances at line {line}: {text}")

    def get_violations(self):
        return self.violations