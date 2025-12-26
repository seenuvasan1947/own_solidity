# S-REEN-004: Benign Reentrancy
# Detects reentrancy that doesn't involve critical state changes
# Lower severity but still worth noting for code quality

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class ReentrancyBenignDetector(SolidityParserListener):
    
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
            self._analyze_benign_reentrancy()
        
        self.in_function = False
        self.function_name = None

    def enterStatement(self, ctx):
        if self.in_function:
            self.function_body.append((ctx.start.line, ctx.getText()))

    def _analyze_benign_reentrancy(self):
        external_calls = []
        state_writes = []
        
        for line, stmt in self.function_body:
            if self._is_external_call(stmt):
                external_calls.append(line)
            
            if self._is_state_write(stmt):
                state_writes.append((line, stmt))
        
        # Check for state writes after calls that don't involve critical variables
        for write_line, write_stmt in state_writes:
            calls_before = [c for c in external_calls if c < write_line]
            
            if calls_before and not self._is_critical_write(write_stmt):
                self.violations.append(
                    f"ℹ️  [S-REEN-004] INFO: Benign reentrancy in function '{self.function_name}' of contract '{self.current_contract}': "
                    f"State write at line {write_line} after external call at line {calls_before[-1]}. "
                    f"While not critical, consider applying check-effects-interactions pattern for consistency."
                )
                return  # Report once

    def _is_external_call(self, stmt):
        patterns = [r'\.call\s*[\(\{]', r'\.delegatecall\s*\(', r'\w+\.\w+\s*\(']
        if 'this.' in stmt or 'super.' in stmt:
            return False
        return any(re.search(p, stmt) for p in patterns)

    def _is_state_write(self, stmt):
        return bool(re.search(r'(\w+)(?:\[.*\])?\s*=', stmt))

    def _is_critical_write(self, stmt):
        critical_keywords = ['balance', 'amount', 'deposit', 'withdraw', 'fund', 'owner', 'admin']
        return any(kw in stmt.lower() for kw in critical_keywords)

    def get_violations(self):
        return self.violations
