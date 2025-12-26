# S-VAL-001: Missing Zero Address Validation
# Detects missing zero address checks for address parameters and state variables
# Critical for preventing accidental loss of ownership or funds

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class MissingZeroAddressDetector(SolidityParserListener):
    """
    Detects missing zero address validation for address parameters.
    
    This detector identifies:
    1. Address parameters in public/external functions without zero checks
    2. State variable assignments from address parameters
    3. Critical operations (transfer, send, call) with unchecked addresses
    
    False Positive Mitigation:
    - Checks for require/assert statements validating the address
    - Excludes view/pure functions
    - Excludes internal/private functions (lower risk)
    - Checks for modifier-based validation
    - Excludes msg.sender (always valid)
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None
        self.function_start_line = None
        self.function_visibility = None
        self.function_state_mutability = None
        self.address_params = set()
        self.validated_addresses = set()
        self.function_modifiers = []
        self.has_zero_check_modifier = False
        self.state_var_assignments = []
        self.critical_operations = []

    def enterContractDefinition(self, ctx):
        """Track current contract"""
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"

    def exitContractDefinition(self, ctx):
        """Reset contract context"""
        self.current_contract = None

    def enterFunctionDefinition(self, ctx):
        """Analyze function for missing zero address checks"""
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "constructor"
        self.function_start_line = ctx.start.line
        self.address_params = set()
        self.validated_addresses = set()
        self.function_modifiers = []
        self.has_zero_check_modifier = False
        self.state_var_assignments = []
        self.critical_operations = []
        
        # Extract function properties
        self._extract_function_properties(ctx)
        
        # Extract address parameters
        self._extract_address_parameters(ctx)

    def _extract_function_properties(self, ctx):
        """Extract visibility and state mutability"""
        text = ctx.getText().lower()
        
        # Extract visibility
        if 'public' in text:
            self.function_visibility = 'public'
        elif 'external' in text:
            self.function_visibility = 'external'
        elif 'internal' in text:
            self.function_visibility = 'internal'
        elif 'private' in text:
            self.function_visibility = 'private'
        else:
            self.function_visibility = 'public'  # Default
        
        # Extract state mutability
        if 'view' in text:
            self.function_state_mutability = 'view'
        elif 'pure' in text:
            self.function_state_mutability = 'pure'
        else:
            self.function_state_mutability = 'mutable'
        
        # Extract modifiers
        self._extract_modifiers(ctx)

    def _extract_modifiers(self, ctx):
        """Extract function modifiers"""
        try:
            if hasattr(ctx, 'modifierList') and ctx.modifierList():
                modifier_list = ctx.modifierList()
                if hasattr(modifier_list, 'modifierInvocation'):
                    modifiers = modifier_list.modifierInvocation()
                    if modifiers:
                        for mod in modifiers:
                            if hasattr(mod, 'identifier') and mod.identifier():
                                mod_name = mod.identifier().getText().lower()
                                self.function_modifiers.append(mod_name)
                                
                                # Check for common zero-check modifiers
                                if any(pattern in mod_name for pattern in ['validaddress', 'nonzero', 'notzero']):
                                    self.has_zero_check_modifier = True
        except Exception:
            pass

    def _extract_address_parameters(self, ctx):
        """Extract address-type parameters"""
        try:
            if hasattr(ctx, 'parameterList') and ctx.parameterList():
                param_list = ctx.parameterList()
                if hasattr(param_list, 'parameter'):
                    params = param_list.parameter()
                    if params:
                        for param in params:
                            if hasattr(param, 'typeName') and param.typeName():
                                type_text = param.typeName().getText().lower()
                                if 'address' in type_text:
                                    if hasattr(param, 'identifier') and param.identifier():
                                        param_name = param.identifier().getText()
                                        # Exclude msg.sender-like parameters
                                        if param_name != 'sender' or 'msg' not in param_name:
                                            self.address_params.add(param_name)
        except Exception:
            pass

    def enterStatement(self, ctx):
        """Check statements for validation and usage"""
        if not self.in_function:
            return
        
        statement_text = ctx.getText()
        
        # Check for zero address validation
        self._check_zero_validation(statement_text)
        
        # Check for state variable assignments
        self._check_state_assignments(statement_text)
        
        # Check for critical operations
        self._check_critical_operations(statement_text)

    def _check_zero_validation(self, text):
        """Check if statement validates zero address"""
        text_lower = text.lower()
        
        # Common zero address validation patterns
        zero_patterns = [
            'address(0)', '0x0', 'address(0x0)',
            '!=address(0)', '!=0x0', '==address(0)', '==0x0'
        ]
        
        # Check if any address parameter is being validated
        for param in self.address_params:
            param_lower = param.lower()
            # Check if parameter is in a require/assert with zero check
            if param_lower in text_lower:
                if ('require(' in text_lower or 'assert(' in text_lower):
                    if any(pattern in text_lower for pattern in zero_patterns):
                        self.validated_addresses.add(param)

    def _check_state_assignments(self, text):
        """Check for state variable assignments from address parameters"""
        for param in self.address_params:
            # Simple pattern: stateVar = param
            if f'={param}' in text or f'= {param}' in text:
                # Check if it's a state variable assignment (contains =)
                if '=' in text and not '==' in text:
                    self.state_var_assignments.append((param, text))

    def _check_critical_operations(self, text):
        """Check for critical operations with address parameters"""
        text_lower = text.lower()
        critical_ops = ['.transfer(', '.send(', '.call(', '.delegatecall(']
        
        for param in self.address_params:
            if param.lower() in text_lower:
                if any(op in text_lower for op in critical_ops):
                    self.critical_operations.append((param, text))

    def exitFunctionDefinition(self, ctx):
        """Check for violations when exiting function"""
        # Skip if no address parameters
        if not self.address_params:
            self.in_function = False
            return
        
        # Skip view/pure functions (no state changes)
        if self.function_state_mutability in ['view', 'pure']:
            self.in_function = False
            return
        
        # Skip internal/private functions (lower risk)
        if self.function_visibility in ['internal', 'private']:
            self.in_function = False
            return
        
        # Skip if has zero-check modifier
        if self.has_zero_check_modifier:
            self.in_function = False
            return
        
        # Check each address parameter
        for param in self.address_params:
            # Skip if validated
            if param in self.validated_addresses:
                continue
            
            # Check if used in state assignments or critical operations
            used_in_state = any(param == p for p, _ in self.state_var_assignments)
            used_in_critical = any(param == p for p, _ in self.critical_operations)
            
            if used_in_state or used_in_critical:
                # High priority - used in critical operations without validation
                self.violations.append(
                    f"❌ [S-VAL-001] CRITICAL: Missing zero address check in function '{self.function_name}' of contract '{self.current_contract}' at line {self.function_start_line}: "
                    f"Address parameter '{param}' is used {'in state variable assignment' if used_in_state else 'in critical operation'} without zero address validation."
                )
            elif self.function_visibility == 'external' or self.function_visibility == 'public':
                # Medium priority - public/external function with address param
                self.violations.append(
                    f"⚠️  [S-VAL-001] WARNING: Missing zero address check in function '{self.function_name}' of contract '{self.current_contract}' at line {self.function_start_line}: "
                    f"Address parameter '{param}' lacks zero address validation. Consider adding 'require({param} != address(0), \"Zero address\");'"
                )
        
        self.in_function = False

    def get_violations(self):
        """Return all detected violations"""
        return self.violations
