# S-ATR-005: Locked Ether
# Detects contracts that can receive ether but cannot withdraw it
# Based on Slither's locked_ether detector
# Impact: MEDIUM | Confidence: HIGH

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class LockedEtherDetector(SolidityParserListener):
    """
    Detects contracts that can receive Ether but have no way to withdraw it.
    
    Vulnerability: If a contract has payable functions but no withdrawal mechanism,
    all Ether sent to it will be permanently locked.
    
    Example (BAD):
        contract Locked {
            function receive() payable public {
                // Accepts ether but no way to withdraw
            }
        }
    
    Recommendation: Add a withdrawal function, remove payable modifier,
    or add selfdestruct capability.
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.contract_line = None
        self.has_payable_function = False
        self.has_withdrawal_mechanism = False
        self.payable_functions = []
    
    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.contract_line = ctx.start.line
        self.has_payable_function = False
        self.has_withdrawal_mechanism = False
        self.payable_functions = []
    
    def exitContractDefinition(self, ctx):
        # Check if contract locks ether
        if self.has_payable_function and not self.has_withdrawal_mechanism:
            funcs_str = ", ".join(self.payable_functions)
            self.violations.append(
                f"❌ [S-ATR-005] Contract '{self.current_contract}' at line {self.contract_line} "
                f"can receive Ether (payable functions: {funcs_str}) "
                f"but has no withdrawal mechanism. Ether sent to this contract will be locked. "
                f"Add a withdrawal function or remove payable modifiers."
            )
        
        self.current_contract = None
    
    def enterFunctionDefinition(self, ctx):
        func_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        
        # Check for payable modifier
        for modifier in ctx.stateMutability():
            if modifier.getText() == "payable":
                self.has_payable_function = True
                self.payable_functions.append(func_name)
                break
        
        # Check for withdrawal mechanisms
        # Look for transfer, send, call with value, or selfdestruct
        func_text = ctx.getText().lower()
        
        withdrawal_patterns = [
            ".transfer(",
            ".send(",
            ".call{value:",
            "selfdestruct(",
            "suicide("
        ]
        
        if any(pattern in func_text for pattern in withdrawal_patterns):
            self.has_withdrawal_mechanism = True
    
    # Also check for receive() and fallback() functions
    def enterReceiveFunctionDefinition(self, ctx):
        self.has_payable_function = True
        self.payable_functions.append("receive()")
    
    def enterFallbackFunctionDefinition(self, ctx):
        # Check if fallback is payable
        for modifier in ctx.stateMutability():
            if modifier.getText() == "payable":
                self.has_payable_function = True
                self.payable_functions.append("fallback()")
                break
    
    def get_violations(self):
        return self.violations
