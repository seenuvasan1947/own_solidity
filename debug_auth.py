from rules.InsufficientAuthorizationDetector import InsufficientAuthorizationDetector
from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser

# Add debug output to the detector
class DebugAuthDetector(InsufficientAuthorizationDetector):
    def enterExpressionStatement(self, ctx):
        if self.current_function and 'require' in ctx.getText():
            text = ctx.getText()
            print(f"Found require in function {self.current_function}: {text}")
            print(f"Available patterns: {self.auth_patterns}")
            for pattern in self.auth_patterns:
                if pattern in text:
                    print(f"  Matched pattern: {pattern}")
        super().enterExpressionStatement(ctx)

input_stream = FileStream('test/InsufficientAuthorization.sol')
lexer = SolidityLexer(input_stream)
stream = CommonTokenStream(lexer)
parser = SolidityParser(stream)
tree = parser.sourceUnit()
walker = ParseTreeWalker()
detector = DebugAuthDetector()
walker.walk(detector, tree)

print('Contract functions:')
for contract_name, functions in detector.contract_functions.items():
    print(f'\n{contract_name}:')
    for func in functions:
        print(f'  {func["name"]}: has_auth_modifier={func["has_auth_modifier"]}, has_auth_require={func["has_auth_require"]}')

print('\nViolations:')
for v in detector.get_violations():
    print(f'  {v}')
