# S-REEN-003: Reentrancy with Events
# Detects reentrancy where events are emitted after external calls
# Can lead to incorrect event ordering and off-chain data inconsistencies

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class ReentrancyEventsDetector(SolidityParserListener):
    
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
            self._analyze_event_reentrancy()
        
        self.in_function = False
        self.function_name = None

    def enterStatement(self, ctx):
        if self.in_function:
            self.function_body.append((ctx.start.line, ctx.getText()))

    def _analyze_event_reentrancy(self):
        external_calls = []
        events = []
        
        for line, stmt in self.function_body:
            if self._is_external_call(stmt):
                external_calls.append(line)
            
            if 'emit' in stmt.lower():
                events.append((line, stmt))
        
        # Check if events are emitted after external calls
        for event_line, event_stmt in events:
            calls_before = [c for c in external_calls if c < event_line]
            
            if calls_before:
                event_name = self._extract_event_name(event_stmt)
                self.violations.append(
                    f"⚠️  [S-REEN-003] LOW: Event emission after external call in function '{self.function_name}' of contract '{self.current_contract}': "
                    f"Event '{event_name}' emitted at line {event_line} after external call at line {calls_before[-1]}. "
                    f"This can lead to incorrect event ordering if the function is re-entered. "
                    f"Emit events before external calls."
                )

    def _is_external_call(self, stmt):
        patterns = [r'\.call\s*[\(\{]', r'\.delegatecall\s*\(', r'\w+\.\w+\s*\(']
        if 'this.' in stmt or 'super.' in stmt or 'emit' in stmt.lower():
            return False
        return any(re.search(p, stmt) for p in patterns)

    def _extract_event_name(self, stmt):
        match = re.search(r'emit\s+(\w+)', stmt, re.IGNORECASE)
        return match.group(1) if match else "unknown"

    def get_violations(self):
        return self.violations
