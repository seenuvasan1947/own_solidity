
from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class FunctionDefinitionListener(SolidityParserListener):
    def enterFunctionDefinition(self, ctx):
        func_name = ctx.identifier().getText() if ctx.identifier() else "<anonymous>"
        print(f"Function found: {func_name} at line {ctx.start.line}")
