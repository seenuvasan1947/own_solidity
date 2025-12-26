# S-REEN-001: Reentrancy with Ether Transfer
# Detects reentrancy vulnerabilities where external calls are made before state updates
# and Ether is transferred, allowing attackers to drain funds

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class ReentrancyEthDetector(SolidityParserListener):
    
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
        self.has_nonreentrant = 'nonReentrant' in func_text or 'noReentrancy' in func_text

    def exitFunctionDefinition(self, ctx):
        if self.in_function and not self.has_nonreentrant:
            self._analyze_reentrancy()
        
        self.in_function = False
        self.function_name = None
        self.function_body = []

    def enterStatement(self, ctx):
        if self.in_function:
            stmt_text = ctx.getText()
            line = ctx.start.line
            self.function_body.append((line, stmt_text))

    def _analyze_reentrancy(self):
        external_calls = []
        eth_transfers = []
        state_writes = []
        
        for line, stmt in self.function_body:
            # Detect external calls
            if self._is_external_call(stmt):
                external_calls.append((line, stmt))
            
            # Detect ETH transfers
            if self._is_eth_transfer(stmt):
                eth_transfers.append((line, stmt))
            
            # Detect state variable writes
            if self._is_state_write(stmt):
                state_writes.append((line, stmt))
        
        # Check for reentrancy pattern: external call/ETH transfer before state update
        for ext_line, ext_stmt in external_calls + eth_transfers:
            for state_line, state_stmt in state_writes:
                if state_line > ext_line:
                    # Extract variable being written
                    var_match = re.search(r'(\w+)\s*[\[\.]', state_stmt)
                    if var_match:
                        var_name = var_match.group(1)
                        
                        # Check if variable was read before the call
                        read_before = any(
                            var_name in s and l < ext_line 
                            for l, s in self.function_body
                        )
                        
                        if read_before or self._is_balance_update(state_stmt):
                            self.violations.append(
                                f"❌ [S-REEN-001] HIGH: Reentrancy vulnerability in function '{self.function_name}' of contract '{self.current_contract}': "
                                f"External call at line {ext_line} before state update at line {state_line}. "
                                f"An attacker can re-enter and exploit the outdated state. "
                                f"Apply check-effects-interactions pattern: update state before external calls."
                            )
                            return  # Report once per function

    def _is_external_call(self, stmt):
        patterns = [
            r'\.call\s*[\(\{]',
            r'\.delegatecall\s*\(',
            r'\.staticcall\s*\(',
            r'\w+\.\w+\s*\(',  # External contract call
        ]
        
        # Exclude internal calls and known safe patterns
        if 'this.' in stmt or 'super.' in stmt:
            return False
        
        return any(re.search(p, stmt) for p in patterns)

    def _is_eth_transfer(self, stmt):
        patterns = [
            r'\.transfer\s*\(',
            r'\.send\s*\(',
            r'\.call\s*\{.*value.*\}',
        ]
        return any(re.search(p, stmt) for p in patterns)

    def _is_state_write(self, stmt):
        # Simple heuristic: assignment with mapping or state variable
        return bool(re.search(r'(\w+)\[.*\]\s*=', stmt) or 
                   re.search(r'(\w+)\s*=\s*[^=]', stmt))

    def _is_balance_update(self, stmt):
        balance_keywords = ['balance', 'amount', 'deposit', 'withdraw', 'fund']
        return any(kw in stmt.lower() for kw in balance_keywords)

    def get_violations(self):
        return self.violations
