# S-ERC-009: Token Reentrancy in transfer/transferFrom
# Detects tokens (ERC223/ERC777) that make external calls in transfer functions
# Can enable reentrancy attacks on third-party contracts using the token

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class TokenReentrancyDetector(SolidityParserListener):
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None
        self.function_start_line = None
        self.is_transfer_function = False
        self.function_body = []

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"

    def exitContractDefinition(self, ctx):
        self.current_contract = None

    def enterFunctionDefinition(self, ctx):
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.function_start_line = ctx.start.line
        self.function_body = []
        
        # Check if this is a transfer or transferFrom function
        self.is_transfer_function = self.function_name in ['transfer', 'transferFrom']

    def exitFunctionDefinition(self, ctx):
        if self.in_function and self.is_transfer_function:
            self._analyze_token_reentrancy()
        
        self.in_function = False
        self.function_name = None
        self.is_transfer_function = False

    def enterStatement(self, ctx):
        if self.in_function and self.is_transfer_function:
            self.function_body.append((ctx.start.line, ctx.getText()))

    def _analyze_token_reentrancy(self):
        external_calls = []
        
        for line, stmt in self.function_body:
            # Check for external calls to user-controlled addresses
            if self._is_external_call_to_param(stmt):
                external_calls.append((line, stmt))
        
        if external_calls:
            for call_line, call_stmt in external_calls:
                self.violations.append(
                    f"⚠️  [S-ERC-009] MEDIUM: Token reentrancy risk in function '{self.function_name}' of contract '{self.current_contract}' at line {call_line}: "
                    f"External call in transfer function can enable reentrancy attacks on third-party contracts. "
                    f"Tokens like ERC223/ERC777 with callbacks in transfer can be exploited. "
                    f"Document this behavior clearly and consider using ERC20 standard without callbacks."
                )

    def _is_external_call_to_param(self, stmt):
        # Check for calls to addresses that might be parameters (to, from, msg.sender)
        patterns = [
            r'(to|from|msg\.sender|tx\.origin)\.call',
            r'(to|from|msg\.sender|tx\.origin)\.\w+\s*\(',
        ]
        
        for pattern in patterns:
            if re.search(pattern, stmt):
                return True
        
        return False

    def get_violations(self):
        return self.violations
