from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class DustAttackDetector(SolidityParserListener):
    def __init__(self):
        self.violations = []
        self.in_function = False
        self.function_name = None

    def enterFunctionDefinition(self, ctx):
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"

    def exitFunctionDefinition(self, ctx):
        self.in_function = False
        self.function_name = None

    def enterExpressionStatement(self, ctx):
        if self.in_function:
            expression_text = ctx.getText()
            if "msg.value" in expression_text and (("< 0.001 ether" in expression_text) or ("< 1000000000000000" in expression_text) or ("< 1 gwei" in expression_text)):
              line = ctx.start.line
              self.violations.append(f"❌ Potential Dust Attack vulnerability in function '{self.function_name}' at line {line}: Checks on msg.value may be vulnerable to dust attacks. {expression_text}")


    def get_violations(self):
        return self.violations