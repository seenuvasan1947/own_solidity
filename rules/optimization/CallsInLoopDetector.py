# S-OPT-003: Calls in Loop Detection
# Detects external calls inside loops which can lead to DoS
# If one call fails, the entire transaction reverts

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class CallsInLoopDetector(SolidityParserListener):
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None
        self.loop_depth = 0
        self.calls_in_loop = []

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"

    def exitContractDefinition(self, ctx):
        self.current_contract = None

    def enterFunctionDefinition(self, ctx):
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.loop_depth = 0
        self.calls_in_loop = []

    def exitFunctionDefinition(self, ctx):
        if self.calls_in_loop:
            calls_desc = ', '.join([f"line {line}" for line in self.calls_in_loop])
            self.violations.append(
                f"⚠️  [S-OPT-003] LOW: External calls in loop in function '{self.function_name}' of contract '{self.current_contract}': "
                f"Calls at {calls_desc}. "
                f"If one call fails, entire transaction reverts. Consider pull over push pattern."
            )
        
        self.in_function = False
        self.function_name = None

    def enterForStatement(self, ctx):
        if self.in_function:
            self.loop_depth += 1

    def exitForStatement(self, ctx):
        if self.in_function:
            self.loop_depth -= 1

    def enterWhileStatement(self, ctx):
        if self.in_function:
            self.loop_depth += 1

    def exitWhileStatement(self, ctx):
        if self.in_function:
            self.loop_depth -= 1

    def enterStatement(self, ctx):
        if not self.in_function or self.loop_depth == 0:
            return
        
        stmt_text = ctx.getText()
        line = ctx.start.line
        
        # Detect external calls
        call_patterns = [
            r'\.call\s*[\(\{]',
            r'\.delegatecall\s*\(',
            r'\.transfer\s*\(',
            r'\.send\s*\(',
            r'\w+\.\w+\s*\(',  # External contract call
        ]
        
        # Exclude internal/library calls
        if 'this.' in stmt_text or 'super.' in stmt_text:
            return
        
        for pattern in call_patterns:
            if re.search(pattern, stmt_text):
                self.calls_in_loop.append(line)
                break

    def get_violations(self):
        return self.violations
