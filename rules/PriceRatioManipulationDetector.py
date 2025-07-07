from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class PriceRatioManipulationDetector(SolidityParserListener):
    def __init__(self):
        self.violations = []
        self.in_function_definition = False
        self.current_function_name = None

    def enterFunctionDefinition(self, ctx):
        self.in_function_definition = True
        self.current_function_name = ctx.identifier().getText() if ctx.identifier() else "anonymous"

    def exitFunctionDefinition(self, ctx):
        self.in_function_definition = False
        self.current_function_name = None

    def enterMulDivModOperation(self, ctx):
        # Check if inside a function and if the operation involves identifiers that might represent token balances
        if self.in_function_definition:
            text = ctx.getText()
            # Simple heuristic: Look for division or multiplication of variables.  A more robust solution would analyze the types of the variables.
            if "/" in text or "*" in text:
                # Extract the expressions on either side of the operator
                left = ctx.expression(0).getText()
                right = ctx.expression(1).getText()
                
                # Check if both sides are simple identifiers (likely token balances)
                if left.isidentifier() and right.isidentifier():

                    line = ctx.start.line
                    self.violations.append(f"⚠️ Price calculated by ratio of token balances in function {self.current_function_name} at line {line}: {text}")

    def get_violations(self):
        return self.violations