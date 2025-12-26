# S-SEC-024: Controlled Delegatecall
# Detects delegatecall to user-controlled addresses
# Allows attacker to execute arbitrary code in contract context

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class ControlledDelegatecallDetector(SolidityParserListener):
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None
        self.function_params = set()
        self.is_upgradeable_proxy = False

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"
        # Simple heuristic for upgradeable proxy
        contract_text = ctx.getText()
        self.is_upgradeable_proxy = 'Proxy' in self.current_contract or 'upgradeable' in contract_text.lower()

    def exitContractDefinition(self, ctx):
        self.current_contract = None

    def enterFunctionDefinition(self, ctx):
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.function_params = set()
        
        # Extract function parameters
        func_text = ctx.getText()
        params = re.findall(r'address\s+(\w+)', func_text)
        self.function_params.update(params)
        
        # Check if function is protected (onlyOwner, etc.)
        self.is_protected = any(mod in func_text for mod in ['onlyOwner', 'onlyAdmin', 'onlyGovernance'])

    def exitFunctionDefinition(self, ctx):
        self.in_function = False
        self.function_name = None

    def enterStatement(self, ctx):
        if not self.in_function:
            return
        
        # Skip if upgradeable proxy with protected function
        if self.is_upgradeable_proxy and self.is_protected:
            return
        
        stmt_text = ctx.getText()
        line = ctx.start.line
        
        # Detect delegatecall
        if '.delegatecall(' in stmt_text or '.callcode(' in stmt_text:
            # Check if destination is user-controlled
            is_user_controlled = False
            
            # Check if using function parameter
            for param in self.function_params:
                if param in stmt_text:
                    is_user_controlled = True
                    break
            
            # Check if using msg.sender or similar
            if 'msg.sender' in stmt_text or 'tx.origin' in stmt_text:
                is_user_controlled = True
            
            if is_user_controlled:
                call_type = 'delegatecall' if '.delegatecall(' in stmt_text else 'callcode'
                self.violations.append(
                    f"❌ [S-SEC-024] HIGH: Controlled {call_type} in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                    f"{call_type.capitalize()} to user-controlled address detected. "
                    f"Attacker can execute arbitrary code in contract context. "
                    f"Use only trusted, hardcoded destinations or implement strict access control."
                )

    def get_violations(self):
        return self.violations
