from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class PriceManipulationDetector(SolidityParserListener):
    def __init__(self):
        self.in_function = False
        self.current_function_name = None
        self.violations = []

    def enterFunctionDefinition(self, ctx):
        self.in_function = True
        self.current_function_name = ctx.identifier().getText() if ctx.identifier() else 'anonymous'

    def exitFunctionDefinition(self, ctx):
        self.in_function = False
        self.current_function_name = None

    def enterExpression(self, ctx:SolidityParser.ExpressionContext):
        # Detect price calculation by ratio of token balances
        if self.in_function:
            text = ctx.getText()
            if "/" in text and ("balanceOf" in text) and ("*" not in text) and ("Chainlink" not in text):
                line = ctx.start.line
                self.violations.append(f"❌ Potential price manipulation vulnerability in function '{self.current_function_name}' at line {line}: Price calculated by ratio of token balances.")

    def get_violations(self):
        return self.violations