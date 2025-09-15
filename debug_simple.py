from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

# Simple test to see what methods are called
class DebugListener(SolidityParserListener):
    def enterExpressionStatement(self, ctx):
        text = ctx.getText()
        if 'require' in text:
            print(f"ExpressionStatement with require: {text}")
    
    def enterFunctionDefinition(self, ctx):
        print(f"FunctionDefinition: {ctx.getText()}")
    
    def enterContractDefinition(self, ctx):
        print(f"ContractDefinition: {ctx.getText()}")
    
    def enterEveryRule(self, ctx):
        pass

input_stream = FileStream('test/InsufficientAuthorization.sol')
lexer = SolidityLexer(input_stream)
stream = CommonTokenStream(lexer)
parser = SolidityParser(stream)
tree = parser.sourceUnit()
walker = ParseTreeWalker()
listener = DebugListener()
walker.walk(listener, tree)
