# S-CODE-020: Assembly Usage Detection
# Detects usage of inline assembly which is error-prone
# Assembly bypasses Solidity safety features

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class AssemblyUsageDetector(SolidityParserListener):
    
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

    def enterAssemblyStatement(self, ctx):
        if self.in_function:
            line = ctx.start.line
            self.violations.append(
                f"ℹ️  [S-CODE-020] INFO: Inline assembly usage in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                f"Assembly bypasses Solidity's safety features and is error-prone. "
                f"Avoid using assembly unless absolutely necessary and ensure thorough review."
            )

    def get_violations(self):
        return self.violations
