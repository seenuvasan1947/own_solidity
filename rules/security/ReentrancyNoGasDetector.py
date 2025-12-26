# S-REEN-005: Reentrancy via send/transfer
# Detects reentrancy through send() and transfer() which can be exploited if gas costs change
# While these have gas limits, they're not foolproof protection

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class ReentrancyNoGasDetector(SolidityParserListener):
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None
        self.function_start_line = None
        self.function_body = []
        self.has_nonreentrant = False

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"

    def exitContractDefinition(self, ctx):
        self.current_contract = None

    def enterFunctionDefinition(self, ctx):
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.function_start_line = ctx.start.line
        self.function_body = []
        
        func_text = ctx.getText()
        self.has_nonreentrant = 'nonReentrant' in func_text

    def exitFunctionDefinition(self, ctx):
        if self.in_function and not self.has_nonreentrant:
            self._analyze_send_transfer_reentrancy()
        
        self.in_function = False
        self.function_name = None

    def enterStatement(self, ctx):
        if self.in_function:
            self.function_body.append((ctx.start.line, ctx.getText()))

    def _analyze_send_transfer_reentrancy(self):
        send_transfer_calls = []
        state_writes = []
        events = []
        
        for line, stmt in self.function_body:
            # Detect send/transfer calls
            if re.search(r'\.send\s*\(', stmt) or re.search(r'\.transfer\s*\(', stmt):
                send_transfer_calls.append((line, stmt))
            
            # Detect state writes
            if self._is_state_write(stmt):
                state_writes.append((line, stmt))
            
            # Detect events
            if 'emit' in stmt.lower():
                events.append((line, stmt))
        
        # Check for state writes or events after send/transfer
        for call_line, call_stmt in send_transfer_calls:
            # Check state writes after
            writes_after = [(l, s) for l, s in state_writes if l > call_line]
            events_after = [(l, s) for l, s in events if l > call_line]
            
            if writes_after or events_after:
                call_type = 'send' if '.send(' in call_stmt else 'transfer'
                self.violations.append(
                    f"ℹ️  [S-REEN-005] INFO: Potential reentrancy via {call_type}() in function '{self.function_name}' of contract '{self.current_contract}' at line {call_line}: "
                    f"State changes or events after {call_type}(). While {call_type}() has gas limits, "
                    f"future gas cost changes could enable reentrancy. Apply check-effects-interactions pattern."
                )
                return  # Report once

    def _is_state_write(self, stmt):
        return bool(re.search(r'(\w+)(?:\[.*\])?\s*=', stmt))

    def get_violations(self):
        return self.violations
