from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class PriceRatioManipulationDetector(SolidityParserListener):
    def __init__(self):
        self.violations = []
        self.in_function = False
        self.current_function_name = None

    def enterFunctionDefinition(self, ctx):
        self.in_function = True
        if ctx.identifier():
            self.current_function_name = ctx.identifier().getText()
        else:
            self.current_function_name = None #anonymous function

    def exitFunctionDefinition(self, ctx):
        self.in_function = False
        self.current_function_name = None

    def enterFunctionCall(self, ctx):
        if not self.in_function:
            return

        function_call_text = ctx.getText().lower()
        #Simplified detection for direct DEX price usage.  Extend with more DEX names.
        if "uniswap" in function_call_text or "pancakeswap" in function_call_text or "getreserves()" in function_call_text or "getamountsout" in function_call_text:
            line = ctx.start.line
            self.violations.append(f"❌ Price manipulation risk in function '{self.current_function_name}' at line {line}: Direct use of DEX spot price is vulnerable to manipulation.")

    def get_violations(self):
        return self.violations