# S-CODE-015: State Variable Shadowing
# Detects state variables that shadow variables from parent contracts
# Can lead to serious bugs where the wrong variable is modified

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class StateShadowingDetector(SolidityParserListener):
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.parent_contracts = []
        self.parent_state_vars = {}
        self.current_state_vars = []
        self.contract_hierarchy = {}

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.current_state_vars = []
        
        # Extract parent contracts
        contract_text = ctx.getText()
        is_match = re.search(r'is\s+([\w\s,]+)\{', contract_text)
        if is_match:
            parents = [p.strip() for p in is_match.group(1).split(',')]
            self.parent_contracts = parents
            self.contract_hierarchy[self.current_contract] = parents

    def exitContractDefinition(self, ctx):
        # Check for shadowing
        if self.parent_contracts:
            for var_name, var_line in self.current_state_vars:
                # Skip __gap variables (used in upgradeable contracts)
                if var_name.startswith('__gap'):
                    continue
                
                # Check if this variable shadows a parent variable
                for parent in self.parent_contracts:
                    if parent in self.parent_state_vars:
                        if var_name in self.parent_state_vars[parent]:
                            self.violations.append(
                                f"❌ [S-CODE-015] HIGH: State variable shadowing in contract '{self.current_contract}' at line {var_line}: "
                                f"Variable '{var_name}' shadows variable from parent contract '{parent}'. "
                                f"This can cause serious bugs where the wrong variable is accessed. "
                                f"Rename the variable or use a different name."
                            )
        
        # Store state variables for this contract
        self.parent_state_vars[self.current_contract] = [v[0] for v in self.current_state_vars]
        self.current_contract = None
        self.parent_contracts = []

    def enterStateVariableDeclaration(self, ctx):
        if self.current_contract:
            var_text = ctx.getText()
            # Extract variable name
            match = re.search(r'\b(\w+)\s*(?:=|;)', var_text)
            if match:
                var_name = match.group(1)
                # Skip type names
                if var_name not in ['uint', 'uint256', 'address', 'bool', 'string', 'bytes', 'mapping']:
                    self.current_state_vars.append((var_name, ctx.start.line))

    def get_violations(self):
        return self.violations
