# S-CODE-013: Missing Events for Arithmetic Parameter Changes
# Detects missing event emissions for critical arithmetic parameter changes
# Events are essential for off-chain tracking of price, rate, and limit changes

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class MissingEventsArithmeticDetector(SolidityParserListener):
    """
    Detects missing events for critical arithmetic parameter changes.
    
    This detector identifies:
    1. Functions that modify price/rate/fee parameters without emitting events
    2. Functions with onlyOwner modifiers that change uint/int state variables
    3. State variable assignments used in arithmetic operations
    
    False Positive Mitigation:
    - Only flags protected functions (with modifiers)
    - Ignores functions that already emit events
    - Focuses on uint/int state variables
    - Checks for critical parameter name patterns
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None
        self.function_start_line = None
        self.function_has_event = False
        self.function_has_modifier = False
        self.function_modifies_arithmetic = False
        self.modified_variables = []
        
        # State variables (uint/int type)
        self.state_arithmetic_variables = set()
        
        # Critical arithmetic parameter keywords
        self.arithmetic_keywords = [
            'price', 'rate', 'fee', 'limit', 'threshold', 'amount', 'value',
            'supply', 'balance', 'reward', 'penalty', 'tax', 'commission',
            'interest', 'dividend', 'quota', 'cap', 'floor', 'ceiling'
        ]

    def enterContractDefinition(self, ctx):
        """Track current contract"""
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.state_arithmetic_variables = set()

    def exitContractDefinition(self, ctx):
        """Reset contract context"""
        self.current_contract = None

    def enterStateVariableDeclaration(self, ctx):
        """Track uint/int state variables"""
        var_text = ctx.getText()
        if re.search(r'\b(uint\d*|int\d*)\b', var_text):
            # Extract variable name
            match = re.search(r'(?:uint\d*|int\d*)\s+(?:public\s+|private\s+|internal\s+)?(\w+)', var_text)
            if match:
                var_name = match.group(1)
                self.state_arithmetic_variables.add(var_name)

    def enterFunctionDefinition(self, ctx):
        """Track current function"""
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.function_start_line = ctx.start.line
        self.function_has_event = False
        self.function_has_modifier = False
        self.function_modifies_arithmetic = False
        self.modified_variables = []
        
        # Check for modifiers
        func_text = ctx.getText()
        if self._has_access_control_modifier(func_text):
            self.function_has_modifier = True

    def exitFunctionDefinition(self, ctx):
        """Check if function should emit events"""
        if self.in_function and self.function_has_modifier and self.function_modifies_arithmetic and not self.function_has_event:
            # Check if modified variable is arithmetic-critical
            for var_name in self.modified_variables:
                if self._is_critical_arithmetic_variable(var_name):
                    self.violations.append(
                        f"⚠️  [S-CODE-013] WARNING: Missing event emission in function '{self.function_name}' of contract '{self.current_contract}' at line {self.function_start_line}: "
                        f"Function modifies critical arithmetic parameter '{var_name}' but does not emit an event. "
                        f"Emit an event for off-chain tracking of parameter changes."
                    )
                    break
        
        self.in_function = False
        self.function_name = None

    def enterEmitStatement(self, ctx):
        """Track event emissions"""
        if self.in_function:
            self.function_has_event = True

    def enterStatement(self, ctx):
        """Check for arithmetic state variable modifications"""
        if not self.in_function:
            return
        
        stmt_text = ctx.getText()
        
        # Check for event emission
        if 'emit' in stmt_text.lower():
            self.function_has_event = True
        
        # Check for state variable assignments
        for var_name in self.state_arithmetic_variables:
            # Pattern: varName = ...
            if re.search(rf'\b{var_name}\s*=', stmt_text):
                self.function_modifies_arithmetic = True
                self.modified_variables.append(var_name)

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

    def _is_critical_arithmetic_variable(self, var_name):
        """Check if variable name suggests critical arithmetic parameter"""
        var_lower = var_name.lower()
        return any(keyword in var_lower for keyword in self.arithmetic_keywords)

    def get_violations(self):
        """Return all detected violations"""
        return self.violations
