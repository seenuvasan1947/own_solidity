# S-CODE-034: Function Init State Variables
# Detects state variables initialized with function calls
# Can cause unexpected behavior due to initialization order

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class FunctionInitStateVariablesDetector(SolidityParserListener):
    
    def __init__(self):
        self.violations = []
        self.current_contract = None

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"

    def exitContractDefinition(self, ctx):
        self.current_contract = None

    def enterStateVariableDeclaration(self, ctx):
        var_text = ctx.getText()
        line = ctx.start.line
        
        # Check if state variable is initialized with a function call
        # Pattern: type varName = functionCall()
        if re.search(r'=\s*\w+\s*\(', var_text):
            # Avoid FP: skip pure functions like address(), uint(), type conversions
            if not re.search(r'=\s*(address|uint|uint256|int|bool|bytes)\s*\(', var_text):
                var_match = re.search(r'(\w+)\s*=', var_text)
                if var_match:
                    var_name = var_match.group(1)
                    self.violations.append(
                        f"ℹ️  [S-CODE-034] INFO: State variable initialized with function call in contract '{self.current_contract}' at line {line}: "
                        f"Variable '{var_name}' is initialized with a function call. "
                        f"This can cause unexpected behavior due to initialization order. "
                        f"Consider initializing in constructor instead."
                    )

    def get_violations(self):
        return self.violations
