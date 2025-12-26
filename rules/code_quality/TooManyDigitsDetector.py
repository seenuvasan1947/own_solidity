# S-CODE-029: Too Many Digits
# Detects numeric literals with too many digits
# Hard to read and prone to errors

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class TooManyDigitsDetector(SolidityParserListener):
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"

    def exitContractDefinition(self, ctx):
        self.current_contract = None

    def enterFunctionDefinition(self, ctx):
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"

    def exitFunctionDefinition(self, ctx):
        self.in_function = False
        self.function_name = None

    def enterStatement(self, ctx):
        if not self.in_function:
            return
        
        stmt_text = ctx.getText()
        line = ctx.start.line
        
        # Find numeric literals with 5+ consecutive zeros
        # Exclude hex addresses (0x followed by 40 hex chars)
        numbers = re.findall(r'\b\d+\b', stmt_text)
        
        for num in numbers:
            if '00000' in num:
                # Avoid FP: skip if it's part of a hex address
                if not re.search(r'0x[0-9a-fA-F]{40}', stmt_text):
                    self.violations.append(
                        f"ℹ️  [S-CODE-029] INFO: Too many digits in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                        f"Literal '{num}' has many consecutive zeros. "
                        f"Use ether/wei suffixes (1 ether, 1e18) or scientific notation for readability."
                    )
                    break

    def get_violations(self):
        return self.violations
