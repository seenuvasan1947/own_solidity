# S-DEFI-004: Pyth Unchecked Confidence
# Detects Pyth oracle price usage without checking confidence level
# Low confidence prices can be unreliable

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class PythUncheckedConfidenceDetector(SolidityParserListener):
    
    PYTH_FUNCTIONS = ['getEmaPrice', 'getEmaPriceNoOlderThan', 'getEmaPriceUnsafe', 
                      'getPrice', 'getPriceNoOlderThan', 'getPriceUnsafe']
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None
        self.function_body = []
        self.price_vars = {}  # {var_name: line}

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"

    def exitContractDefinition(self, ctx):
        self.current_contract = None

    def enterFunctionDefinition(self, ctx):
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.function_body = []
        self.price_vars = {}

    def exitFunctionDefinition(self, ctx):
        # Check if confidence is validated
        for var_name, line in self.price_vars.items():
            if not self._is_conf_checked(var_name):
                self.violations.append(
                    f"⚠️  [S-DEFI-004] MEDIUM: Pyth price confidence not checked in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                    f"Price variable '{var_name}' from Pyth oracle is not checked for confidence level. "
                    f"Check price.conf field. Visit https://docs.pyth.network/price-feeds/best-practices#confidence-intervals"
                )
        
        self.in_function = False
        self.function_name = None

    def enterStatement(self, ctx):
        if self.in_function:
            stmt_text = ctx.getText()
            line = ctx.start.line
            self.function_body.append((line, stmt_text))
            
            # Detect Pyth oracle calls
            for func in self.PYTH_FUNCTIONS:
                if f'.{func}(' in stmt_text:
                    var_match = re.search(r'(\w+)\s*=.*\.' + func, stmt_text)
                    if var_match:
                        var_name = var_match.group(1)
                        self.price_vars[var_name] = line

    def _is_conf_checked(self, var_name):
        """Check if confidence field is validated"""
        for line, stmt in self.function_body:
            if f'{var_name}.conf' in stmt:
                return True
        return False

    def get_violations(self):
        return self.violations
