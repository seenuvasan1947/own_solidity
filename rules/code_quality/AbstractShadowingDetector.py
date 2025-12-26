# S-CODE-016: Abstract Contract State Variable Shadowing
# Detects state variables shadowing from abstract parent contracts
# Can cause confusion about which variable is being used

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class AbstractShadowingDetector(SolidityParserListener):
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.is_abstract = False
        self.parent_contracts = []
        self.abstract_contracts = set()
        self.abstract_state_vars = {}
        self.current_state_vars = []

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.current_state_vars = []
        
        contract_text = ctx.getText()
        
        # Check if this contract is abstract
        self.is_abstract = 'abstract' in contract_text or 'interface' in contract_text
        
        # Extract parent contracts
        is_match = re.search(r'is\s+([\w\s,]+)\{', contract_text)
        if is_match:
            self.parent_contracts = [p.strip() for p in is_match.group(1).split(',')]

    def exitContractDefinition(self, ctx):
        # Store if abstract
        if self.is_abstract:
            self.abstract_contracts.add(self.current_contract)
            self.abstract_state_vars[self.current_contract] = [v[0] for v in self.current_state_vars]
        
        # Check for shadowing from abstract parents
        if not self.is_abstract and self.parent_contracts:
            for var_name, var_line in self.current_state_vars:
                if var_name.startswith('__gap'):
                    continue
                
                for parent in self.parent_contracts:
                    if parent in self.abstract_contracts:
                        if parent in self.abstract_state_vars:
                            if var_name in self.abstract_state_vars[parent]:
                                self.violations.append(
                                    f"⚠️  [S-CODE-016] MEDIUM: Abstract contract variable shadowing in contract '{self.current_contract}' at line {var_line}: "
                                    f"Variable '{var_name}' shadows variable from abstract parent '{parent}'. "
                                    f"Remove the shadowing variable."
                                )
        
        self.current_contract = None
        self.parent_contracts = []
        self.is_abstract = False

    def enterStateVariableDeclaration(self, ctx):
        if self.current_contract:
            var_text = ctx.getText()
            match = re.search(r'\b(\w+)\s*(?:=|;)', var_text)
            if match:
                var_name = match.group(1)
                if var_name not in ['uint', 'uint256', 'address', 'bool', 'string', 'bytes', 'mapping']:
                    self.current_state_vars.append((var_name, ctx.start.line))

    def get_violations(self):
        return self.violations
