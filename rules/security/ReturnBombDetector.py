# S-SEC-029: Return Bomb
# Detects external calls with gas limits that can be exploited via return bombs
# Callee can return large data causing caller to run out of gas

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class ReturnBombDetector(SolidityParserListener):
    
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
        
        # Detect calls with gas limits that return dynamic types
        # Pattern: .call{gas: ...}(...) or .call{value: ..., gas: ...}(...)
        if re.search(r'\.call\s*\{\s*[^}]*gas\s*:', stmt_text):
            # Check if return value is captured (bytes memory)
            if re.search(r'\(\s*\w+\s*,\s*bytes\s+memory\s+\w+\s*\)', stmt_text) or \
               re.search(r'bytes\s+memory\s+\w+\s*=', stmt_text):
                self.violations.append(
                    f"⚠️  [S-SEC-029] LOW: Potential return bomb in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                    f"External call with gas limit returns dynamic data (bytes). "
                    f"Callee can return large data causing caller OOG. "
                    f"Consider using ExcessivelySafeCall library or avoid decoding large returndata."
                )

    def get_violations(self):
        return self.violations
