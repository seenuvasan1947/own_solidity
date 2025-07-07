from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class PriceManipulationDetector(SolidityParserListener):
    def __init__(self):
        self.violations = []

    def enterFunctionCall(self, ctx):
        # Look for function calls that might be getting spot prices directly.
        # This is a simplified check and can be refined with more specific DEX function names.
        function_text = ctx.getText().lower()
        if ("getprice" in function_text or "currentprice" in function_text or "getPrice" in function_text or "get_price" in function_text) and "twap" not in function_text:  # Add check to exclude TWAP
            line = ctx.start.line
            self.violations.append(f"❌ Possible price manipulation vulnerability at line {line}: Direct DEX price usage detected. Consider using TWAP or oracles. Function Call: {function_text}")

    def get_violations(self):
        return self.violations