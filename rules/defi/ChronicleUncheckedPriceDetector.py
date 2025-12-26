# S-DEFI-003: Chronicle Unchecked Price
# Detects Chronicle oracle usage where returned price is not validated
# Invalid prices can lead to incorrect protocol behavior

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class ChronicleUncheckedPriceDetector(SolidityParserListener):
    
    CHRONICLE_FUNCTIONS = ['read', 'tryRead', 'readWithAge', 'tryReadWithAge', 'latestAnswer', 'latestRoundData']
    
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
        # Check if price variables are validated
        for var_name, line in self.price_vars.items():
            if not self._is_price_checked(var_name):
                self.violations.append(
                    f"⚠️  [S-DEFI-003] MEDIUM: Chronicle price not validated in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                    f"Price variable '{var_name}' from Chronicle oracle is not checked for validity. "
                    f"Add validation: require({var_name} > 0, \"Invalid price\") or check isValid flag."
                )
        
        self.in_function = False
        self.function_name = None

    def enterStatement(self, ctx):
        if self.in_function:
            stmt_text = ctx.getText()
            line = ctx.start.line
            self.function_body.append((line, stmt_text))
            
            # Detect Chronicle oracle calls
            for func in self.CHRONICLE_FUNCTIONS:
                if f'.{func}(' in stmt_text:
                    # Extract variable assignment
                    var_match = re.search(r'(\w+)\s*=.*\.' + func, stmt_text)
                    if var_match:
                        var_name = var_match.group(1)
                        self.price_vars[var_name] = line
                    # Tuple unpacking
                    tuple_match = re.search(r'\((\w+)\s*,', stmt_text)
                    if tuple_match:
                        var_name = tuple_match.group(1)
                        self.price_vars[var_name] = line

    def _is_price_checked(self, var_name):
        """Check if price variable is validated"""
        for line, stmt in self.function_body:
            # Check for require/assert with the variable
            if re.search(rf'require\s*\([^)]*{var_name}', stmt):
                return True
            if re.search(rf'assert\s*\([^)]*{var_name}', stmt):
                return True
            # Check for if statement checking the variable
            if re.search(rf'if\s*\([^)]*{var_name}\s*[><!]=', stmt):
                return True
        
        return False

    def get_violations(self):
        return self.violations
