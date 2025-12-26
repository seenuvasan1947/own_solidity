# S-SEC-025: Delegatecall in Loop (Payable Function)
# Detects delegatecall inside loops in payable functions
# msg.value is reused for each iteration, leading to accounting errors

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class DelegatecallInLoopDetector(SolidityParserListener):
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None
        self.is_payable = False
        self.loop_depth = 0
        self.delegatecalls_in_loop = []

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"

    def exitContractDefinition(self, ctx):
        self.current_contract = None

    def enterFunctionDefinition(self, ctx):
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.loop_depth = 0
        self.delegatecalls_in_loop = []
        
        # Check if function is payable
        func_text = ctx.getText()
        self.is_payable = 'payable' in func_text

    def exitFunctionDefinition(self, ctx):
        if self.is_payable and self.delegatecalls_in_loop:
            calls_desc = ', '.join([f"line {line}" for line in self.delegatecalls_in_loop])
            self.violations.append(
                f"❌ [S-SEC-025] HIGH: Delegatecall in loop within payable function '{self.function_name}' of contract '{self.current_contract}': "
                f"Delegatecalls at {calls_desc}. "
                f"msg.value is reused for each iteration, causing incorrect accounting. "
                f"Ensure delegated function doesn't use msg.value or redesign the logic."
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
        if not self.in_function or self.loop_depth == 0 or not self.is_payable:
            return
        
        stmt_text = ctx.getText()
        line = ctx.start.line
        
        # Detect delegatecall
        if '.delegatecall(' in stmt_text:
            self.delegatecalls_in_loop.append(line)

    def get_violations(self):
        return self.violations
