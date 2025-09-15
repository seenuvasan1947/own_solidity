from SolidityParserListener import SolidityParserListener

class InsecureDelegatecallUsageDetector(SolidityParserListener):
    """
    Rule Code: 003
    Detects SCWE-035: Insecure Delegatecall Usage vulnerabilities
    
    Insecure delegatecall usage refers to vulnerabilities that arise when using delegatecall 
    to execute code from another contract. This can lead to unauthorized access to sensitive 
    functions, exploitation of vulnerabilities in the called contract, and loss of funds or data.
    """
    
    # Constants for delegatecall security patterns
    DELEGATECALL_PATTERNS = ['delegatecall', 'delegateCall']
    ACCESS_CONTROL_PATTERNS = ['onlyowner', 'require', 'modifier', 'authorized', 'permission']
    TRUSTED_TARGET_PATTERNS = ['trusted', 'whitelist', 'allowed', 'approved', 'valid']
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.current_function = None
        self.delegatecall_functions = []
        self.has_access_control = False
        self.has_trusted_targets = False
        self.owner_variable = False
        self.trusted_target_mapping = False
        
    def enterContractDefinition(self, ctx):
        """Track contract definitions and reset tracking variables."""
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "UnknownContract"
        self.delegatecall_functions = []
        self.has_access_control = False
        self.has_trusted_targets = False
        self.owner_variable = False
        self.trusted_target_mapping = False
        
    def exitContractDefinition(self, ctx):
        """Check for missing delegatecall security mechanisms at contract level."""
        if (self.current_contract and self.delegatecall_functions and 
            'secure' not in self.current_contract.lower()):
            if not self.owner_variable and not self.has_access_control:
                self.violations.append(
                    f"SCWE-035: Contract '{self.current_contract}' uses delegatecall "
                    f"but lacks proper access control mechanisms (owner variable or modifiers)."
                )
            if not self.trusted_target_mapping and not self.has_trusted_targets:
                self.violations.append(
                    f"SCWE-035: Contract '{self.current_contract}' uses delegatecall "
                    f"but lacks trusted target validation mechanisms."
                )
        self.current_contract = None
        
    def enterFunctionDefinition(self, ctx):
        """Track function definitions."""
        if not self.current_contract:
            return
            
        func_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.current_function = func_name
        
        # Check for access control modifiers
        func_text = ctx.getText()
        func_text_lower = func_text.lower()
        if any(pattern in func_text_lower for pattern in self.ACCESS_CONTROL_PATTERNS):
            self.has_access_control = True
        
    def exitFunctionDefinition(self, ctx):
        """Check delegatecall functions for security vulnerabilities."""
        if self.current_function and self.delegatecall_functions:
            # Find current function in delegatecall_functions
            current_func_info = None
            for func_info in self.delegatecall_functions:
                if func_info['function'] == self.current_function:
                    current_func_info = func_info
                    break
                    
            if current_func_info:
                # Check for missing security measures
                if not current_func_info['has_access_control']:
                    self.violations.append(
                        f"SCWE-035: Function '{self.current_function}' at line {current_func_info['line']} "
                        f"uses delegatecall without proper access control. "
                        f"Consider adding onlyOwner or similar access restrictions."
                    )
                    
                if not current_func_info['has_target_validation']:
                    self.violations.append(
                        f"SCWE-035: Function '{self.current_function}' at line {current_func_info['line']} "
                        f"uses delegatecall without target validation. "
                        f"Consider validating the target address before delegatecall."
                    )
                    
                if current_func_info['user_controlled_target']:
                    self.violations.append(
                        f"SCWE-035: Function '{self.current_function}' at line {current_func_info['line']} "
                        f"allows user-controlled target address for delegatecall. "
                        f"This can lead to arbitrary code execution vulnerabilities."
                    )
        
        self.current_function = None
        
    def enterStateVariableDeclaration(self, ctx):
        """Check for security-related state variables."""
        if not self.current_contract:
            return
            
        var_name = ctx.identifier().getText() if ctx.identifier() else ""
        var_name_lower = var_name.lower()
        var_text = ctx.getText().lower()
        
        # Check for owner variable
        if 'owner' in var_name_lower:
            self.owner_variable = True
            
        # Check for trusted target mapping or variables
        if any(pattern in var_name_lower for pattern in self.TRUSTED_TARGET_PATTERNS):
            if 'mapping' in var_text:
                self.trusted_target_mapping = True
            else:
                self.has_trusted_targets = True
                
    def enterModifierDefinition(self, ctx):
        """Check for access control modifiers."""
        if not self.current_contract:
            return
            
        modifier_name = ctx.identifier().getText() if ctx.identifier() else ""
        modifier_name_lower = modifier_name.lower()
        
        # Check for access control modifiers
        if any(pattern in modifier_name_lower for pattern in self.ACCESS_CONTROL_PATTERNS):
            self.has_access_control = True
            
    def enterFunctionCall(self, ctx):
        """Check function calls for delegatecall usage."""
        if not self.current_function or not self.current_contract:
            return
            
        call_text = ctx.getText()
        call_text_lower = call_text.lower()
        
        # Check for delegatecall usage
        if any(pattern in call_text_lower for pattern in self.DELEGATECALL_PATTERNS):
            # Don't flag secure functions (those with 'secure' in name are likely examples)
            if 'secure' not in self.current_function.lower():
                # Analyze the delegatecall for security issues
                func_info = {
                    'function': self.current_function,
                    'line': ctx.start.line,
                    'call_text': call_text,
                    'has_access_control': self._check_function_access_control(),
                    'has_target_validation': self._check_target_validation(call_text_lower),
                    'user_controlled_target': self._check_user_controlled_target(call_text)
                }
                self.delegatecall_functions.append(func_info)
            
    def enterMemberAccess(self, ctx):
        """Check member access for delegatecall patterns."""
        if not self.current_function or not self.current_contract:
            return
            
        member_text = ctx.getText()
        member_text_lower = member_text.lower()
        
        # Check for delegatecall member access
        if any(pattern in member_text_lower for pattern in self.DELEGATECALL_PATTERNS):
            # Don't flag secure functions
            if 'secure' not in self.current_function.lower():
                # Get the parent context to analyze the full call
                parent = ctx.parentCtx
                if parent:
                    parent_text = parent.getText()
                    func_info = {
                        'function': self.current_function,
                        'line': ctx.start.line,
                        'call_text': parent_text,
                        'has_access_control': self._check_function_access_control(),
                        'has_target_validation': self._check_target_validation(parent_text.lower()),
                        'user_controlled_target': self._check_user_controlled_target(parent_text)
                    }
                    self.delegatecall_functions.append(func_info)
                
    def _check_function_access_control(self):
        """Check if current function has access control."""
        # This is a simplified check - in practice, we'd need to analyze the full function context
        return self.has_access_control or self.owner_variable
        
    def _check_target_validation(self, call_text_lower):
        """Check if the delegatecall target is validated."""
        # Look for validation patterns in the call context
        validation_patterns = [
            'require(', 'assert(', 'if(', 'trusted', 'whitelist', 
            'allowed', 'approved', 'valid', '!=address(0)'
        ]
        return any(pattern in call_text_lower for pattern in validation_patterns)
        
    def _check_user_controlled_target(self, call_text):
        """Check if the delegatecall target is user-controlled."""
        # Look for function parameters or user input in the target
        user_input_patterns = [
            'target', 'address', 'to', 'contract', '_target', '_address', '_to'
        ]
        
        # Simple heuristic: if the target contains common parameter names, it might be user-controlled
        call_text_lower = call_text.lower()
        
        # Check if target appears to be a parameter (contains parameter-like names)
        for pattern in user_input_patterns:
            if pattern in call_text_lower and not self._is_validated_target(call_text_lower):
                return True
        return False
        
    def _is_validated_target(self, call_text_lower):
        """Check if the target appears to be validated."""
        validation_indicators = [
            'trusted', 'whitelist', 'approved', 'valid', 'require(', 'assert('
        ]
        return any(indicator in call_text_lower for indicator in validation_indicators)
        
    def get_violations(self):
        """Return list of detected violations."""
        return self.violations
