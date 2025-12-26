# S-SEC-028: msg.value in Loop
# Detects msg.value usage inside loops in payable functions
# msg.value is constant per transaction, causing accounting errors

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class MsgValueInLoopDetector(SolidityParserListener):
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None
        self.is_payable = False
        self.loop_depth = 0
        self.msg_value_in_loop = []

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"

    def exitContractDefinition(self, ctx):
        self.current_contract = None

    def enterFunctionDefinition(self, ctx):
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.loop_depth = 0
        self.msg_value_in_loop = []
        
        func_text = ctx.getText()
        self.is_payable = 'payable' in func_text

    def exitFunctionDefinition(self, ctx):
        if self.is_payable and self.msg_value_in_loop:
            calls_desc = ', '.join([f"line {line}" for line in self.msg_value_in_loop])
            self.violations.append(
                f"❌ [S-SEC-028] HIGH: msg.value used in loop in payable function '{self.function_name}' of contract '{self.current_contract}': "
                f"msg.value usage at {calls_desc}. "
                f"msg.value is constant per transaction, causing incorrect accounting in loops. "
                f"Use explicit amount array instead."
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
        
        # Detect msg.value usage
        if 'msg.value' in stmt_text:
            # Avoid FP: skip if checking msg.value == 0
            if not re.search(r'msg\.value\s*==\s*0|0\s*==\s*msg\.value', stmt_text):
                self.msg_value_in_loop.append(line)

    def get_violations(self):
        return self.violations
