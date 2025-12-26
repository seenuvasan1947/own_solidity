# S-DEFI-005: Pyth Unchecked PublishTime
# Detects Pyth oracle price usage without checking publishTime
# Stale prices can lead to incorrect protocol behavior

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class PythUncheckedPublishTimeDetector(SolidityParserListener):
    
    PYTH_FUNCTIONS = ['getEmaPrice', 'getEmaPriceUnsafe', 'getPrice', 'getPriceUnsafe']
    
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
        # Check if publishTime is validated
        for var_name, line in self.price_vars.items():
            if not self._is_publishtime_checked(var_name):
                self.violations.append(
                    f"⚠️  [S-DEFI-005] MEDIUM: Pyth price publishTime not checked in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                    f"Price variable '{var_name}' from Pyth oracle is not checked for publishTime. "
                    f"Check price.publishTime field to ensure price freshness."
                )
        
        self.in_function = False
        self.function_name = None

    def enterStatement(self, ctx):
        if self.in_function:
            stmt_text = ctx.getText()
            line = ctx.start.line
            self.function_body.append((line, stmt_text))
            
            # Detect Pyth oracle calls (excluding NoOlderThan variants which check time)
            for func in self.PYTH_FUNCTIONS:
                if f'.{func}(' in stmt_text:
                    var_match = re.search(r'(\w+)\s*=.*\.' + func, stmt_text)
                    if var_match:
                        var_name = var_match.group(1)
                        self.price_vars[var_name] = line

    def _is_publishtime_checked(self, var_name):
        """Check if publishTime field is validated"""
        for line, stmt in self.function_body:
            if f'{var_name}.publishTime' in stmt:
                return True
        return False

    def get_violations(self):
        return self.violations
