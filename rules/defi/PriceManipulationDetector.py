from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class PriceManipulationDetector(SolidityParserListener):
    def __init__(self):
        self.violations = []

    def enterFunctionCall(self, ctx):
        function_name = ctx.expression().getText()
        #print(f"Function call {function_name=}")

        # check for a basic dex call that is vulnerable
        if "getReserves" in function_name or "getPrice" in function_name or "getAmountsOut" in function_name:

            line = ctx.start.line
            reason = f"❌ Vulnerable DEX spot price usage detected at line {line}: {function_name}. Consider using TWAP or oracles."
            self.violations.append(reason)

    def get_violations(self):
        return self.violations