# S-DEFI-003: Pyth Deprecated Functions
# Detects usage of deprecated Pyth Network oracle functions
# Should use updated API

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class PythDeprecatedFunctionsDetector(SolidityParserListener):
    """
    Detects deprecated Pyth oracle functions.
    
    Deprecated functions:
    - getValidTimePeriod()
    - getEmaPrice()
    - getPrice()
    
    Should use: getPriceUnsafe(), getPriceNoOlderThan(), etc.
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.uses_pyth = False
        
        self.deprecated_functions = [
            'getValidTimePeriod',
            'getEmaPrice',
            'getPrice'
        ]

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.uses_pyth = False

    def enterImportDirective(self, ctx):
        text = ctx.getText()
        if 'IPyth' in text or 'pyth' in text.lower():
            self.uses_pyth = True

    def enterStatement(self, ctx):
        if not self.uses_pyth:
            return
        
        text = ctx.getText()
        line = ctx.start.line
        
        for func in self.deprecated_functions:
            if f'{func}(' in text or f'.{func}(' in text:
                self.violations.append(
                    f"⚠️  [S-DEFI-003] WARNING: Deprecated Pyth function in contract '{self.current_contract}' at line {line}: "
                    f"Function '{func}()' is deprecated. Use getPriceUnsafe() or getPriceNoOlderThan() instead. "
                    f"See https://api-reference.pyth.network/"
                )

    def exitContractDefinition(self, ctx):
        self.current_contract = None

    def get_violations(self):
        return self.violations
