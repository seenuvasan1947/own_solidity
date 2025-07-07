from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class PriceRatioManipulationDetector(SolidityParserListener):
    def __init__(self):
        self.violations = []

    def enterExpression(self, ctx):
        # Look for patterns like `token0.balance() / token1.balance()` or similar patterns
        # that indicate a price calculation based on direct balance ratio.  This is a simplified
        # detection and could be refined further with more sophisticated analysis.
        text = ctx.getText()
        if "/" in text and (".balance()" in text or ".totalSupply()" in text):
            line = ctx.start.line
            self.violations.append(f"❌ Price calculated by ratio of token balances at line {line}: {text}. This is vulnerable to price manipulation.")

    def get_violations(self):
        return self.violations