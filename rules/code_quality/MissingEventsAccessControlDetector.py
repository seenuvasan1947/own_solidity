# S-CODE-012: Missing Events for Access Control Changes
# Detects missing event emissions for critical access control parameter changes
# Events are essential for off-chain tracking of ownership and permission changes

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class MissingEventsAccessControlDetector(SolidityParserListener):
    """
    Detects missing events for critical access control parameter changes.
    
    This detector identifies:
    1. Functions that modify owner/admin addresses without emitting events
    2. Functions with onlyOwner/onlyAdmin modifiers that change addresses
    3. State variable assignments of address type in protected functions
    
    False Positive Mitigation:
    - Only flags protected functions (with modifiers)
    - Ignores functions that already emit events
    - Focuses on address-type state variables
    - Checks for common access control patterns
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None
        self.function_start_line = None
        self.function_has_event = False
        self.function_has_modifier = False
        self.function_modifies_address = False
        self.modified_addresses = []
        
        # State variables (address type)
        self.state_address_variables = set()
        
        # Access control keywords
        self.access_control_keywords = ['owner', 'admin', 'authority', 'controller', 'governance']

    def enterContractDefinition(self, ctx):
        """Track current contract"""
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.state_address_variables = set()

    def exitContractDefinition(self, ctx):
        """Reset contract context"""
        self.current_contract = None

    def enterStateVariableDeclaration(self, ctx):
        """Track address-type state variables"""
        var_text = ctx.getText()
        if 'address' in var_text:
            # Extract variable name
            match = re.search(r'address\s+(?:public\s+|private\s+|internal\s+)?(\w+)', var_text)
            if match:
                var_name = match.group(1)
                self.state_address_variables.add(var_name)

    def enterFunctionDefinition(self, ctx):
        """Track current function"""
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.function_start_line = ctx.start.line
        self.function_has_event = False
        self.function_has_modifier = False
        self.function_modifies_address = False
        self.modified_addresses = []
        
        # Check for modifiers
        func_text = ctx.getText()
        if self._has_access_control_modifier(func_text):
            self.function_has_modifier = True

    def exitFunctionDefinition(self, ctx):
        """Check if function should emit events"""
        if self.in_function and self.function_has_modifier and self.function_modifies_address and not self.function_has_event:
            # Check if modified variable is access-control related
            for var_name in self.modified_addresses:
                if self._is_access_control_variable(var_name):
                    self.violations.append(
                        f"⚠️  [S-CODE-012] WARNING: Missing event emission in function '{self.function_name}' of contract '{self.current_contract}' at line {self.function_start_line}: "
                        f"Function modifies access control variable '{var_name}' but does not emit an event. "
                        f"Emit an event for off-chain tracking of critical parameter changes."
                    )
                    break
        
        self.in_function = False
        self.function_name = None

    def enterEmitStatement(self, ctx):
        """Track event emissions"""
        if self.in_function:
            self.function_has_event = True

    def enterStatement(self, ctx):
        """Check for address state variable modifications"""
        if not self.in_function:
            return
        
        stmt_text = ctx.getText()
        
        # Check for event emission (alternative pattern)
        if 'emit' in stmt_text.lower():
            self.function_has_event = True
        
        # Check for state variable assignments
        for var_name in self.state_address_variables:
            # Pattern: varName = ...
            if re.search(rf'\b{var_name}\s*=', stmt_text):
                self.function_modifies_address = True
                self.modified_addresses.append(var_name)

    def _has_access_control_modifier(self, func_text):
        """Check if function has access control modifiers"""
        access_modifiers = [
            'onlyOwner', 'onlyAdmin', 'onlyGovernance', 'onlyController',
            'onlyAuthorized', 'requiresAuth', 'authorized', 'restricted'
        ]
        
        for modifier in access_modifiers:
            if modifier in func_text:
                return True
        
        return False

    def _is_access_control_variable(self, var_name):
        """Check if variable name suggests access control usage"""
        var_lower = var_name.lower()
        return any(keyword in var_lower for keyword in self.access_control_keywords)

    def get_violations(self):
        """Return all detected violations"""
        return self.violations
