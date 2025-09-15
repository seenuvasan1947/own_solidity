from SolidityParserListener import SolidityParserListener

class InsecureUseOfSelfdestructDetector(SolidityParserListener):
    """
    Rule Code: 006
    Detects SCWE-038: Insecure Use of Selfdestruct vulnerabilities
    
    Insecure use of selfdestruct refers to vulnerabilities that arise when the selfdestruct 
    function is used without proper safeguards. This can lead to unauthorized destruction 
    of the contract, loss of funds or data, and exploitation of vulnerabilities in contract logic.
    """
    
    # Constants for selfdestruct security patterns
    SELFDESTRUCT_PATTERNS = ['selfdestruct(', 'selfdestruct ']
    ACCESS_CONTROL_PATTERNS = ['onlyowner', 'onlyadmin', 'require(', 'modifier', 'authorized']
    ADMIN_ROLE_PATTERNS = ['owner', 'admin', 'manager', 'controller', 'governance']
    CIRCUIT_BREAKER_PATTERNS = ['pause', 'emergency', 'halt', 'stop', 'freeze', 'circuit']
    TIME_LOCK_PATTERNS = ['timelock', 'delay', 'cooldown', 'waiting']
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.current_function = None
        self.selfdestruct_functions = []
        self.has_admin_role = False
        self.has_access_control_modifiers = False
        self.has_circuit_breakers = False
        self.has_time_locks = False
        
    def enterContractDefinition(self, ctx):
        """Track contract definitions and reset tracking variables."""
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "UnknownContract"
        self.selfdestruct_functions = []
        self.has_admin_role = False
        self.has_access_control_modifiers = False
        self.has_circuit_breakers = False
        self.has_time_locks = False
        
    def exitContractDefinition(self, ctx):
        """Check for missing selfdestruct security at contract level."""
        if self.current_contract and self.selfdestruct_functions:
            # Check if contract with selfdestruct has proper security mechanisms
            if not self.has_admin_role and 'secure' not in self.current_contract.lower():
                self.violations.append(
                    f"SCWE-038: Contract '{self.current_contract}' uses selfdestruct "
                    f"but lacks admin role management for access control."
                )
                
            if not self.has_access_control_modifiers and 'secure' not in self.current_contract.lower():
                self.violations.append(
                    f"SCWE-038: Contract '{self.current_contract}' uses selfdestruct "
                    f"but lacks access control modifiers to restrict usage."
                )
        self.current_contract = None
        
    def enterFunctionDefinition(self, ctx):
        """Track function definitions."""
        if not self.current_contract:
            return
            
        func_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.current_function = func_name
        
        # Check for access control in function definition
        func_text = ctx.getText()
        func_text_lower = func_text.lower()
        if any(pattern in func_text_lower for pattern in self.ACCESS_CONTROL_PATTERNS):
            self.has_access_control_modifiers = True
        
    def exitFunctionDefinition(self, ctx):
        """Check selfdestruct functions for security vulnerabilities."""
        if self.current_function and self.selfdestruct_functions:
            # Find current function in selfdestruct_functions
            current_func_info = None
            for func_info in self.selfdestruct_functions:
                if func_info['function'] == self.current_function:
                    current_func_info = func_info
                    break
                    
            if current_func_info:
                # Don't flag secure functions
                if 'secure' not in self.current_function.lower():
                    # Check for missing security measures
                    if not current_func_info['has_access_control']:
                        self.violations.append(
                            f"SCWE-038: Function '{self.current_function}' at line {current_func_info['line']} "
                            f"uses selfdestruct without proper access control. "
                            f"Consider adding onlyOwner or similar restrictions."
                        )
                        
                    if not current_func_info['has_admin_check']:
                        self.violations.append(
                            f"SCWE-038: Function '{self.current_function}' at line {current_func_info['line']} "
                            f"uses selfdestruct without admin authorization checks. "
                            f"Only authorized addresses should be able to destroy the contract."
                        )
                        
                    if current_func_info['public_access']:
                        self.violations.append(
                            f"SCWE-038: Function '{self.current_function}' at line {current_func_info['line']} "
                            f"allows public access to selfdestruct. "
                            f"This creates a critical security vulnerability."
                        )
        
        self.current_function = None
        
    def enterStateVariableDeclaration(self, ctx):
        """Check for admin role and security-related state variables."""
        if not self.current_contract:
            return
            
        var_name = ctx.identifier().getText() if ctx.identifier() else ""
        var_name_lower = var_name.lower()
        
        # Check for admin role variables
        if any(pattern in var_name_lower for pattern in self.ADMIN_ROLE_PATTERNS):
            self.has_admin_role = True
            
        # Check for circuit breaker variables
        if any(pattern in var_name_lower for pattern in self.CIRCUIT_BREAKER_PATTERNS):
            self.has_circuit_breakers = True
            
        # Check for time lock variables
        if any(pattern in var_name_lower for pattern in self.TIME_LOCK_PATTERNS):
            self.has_time_locks = True
            
    def enterModifierDefinition(self, ctx):
        """Check for access control modifiers."""
        if not self.current_contract:
            return
            
        modifier_name = ctx.identifier().getText() if ctx.identifier() else ""
        modifier_name_lower = modifier_name.lower()
        
        # Check for access control modifiers
        if any(pattern in modifier_name_lower for pattern in self.ACCESS_CONTROL_PATTERNS):
            self.has_access_control_modifiers = True
            
    def enterFunctionCall(self, ctx):
        """Check function calls for selfdestruct usage."""
        if not self.current_function or not self.current_contract:
            return
            
        call_text = ctx.getText()
        call_text_lower = call_text.lower()
        
        # Check for selfdestruct usage
        if any(pattern in call_text_lower for pattern in self.SELFDESTRUCT_PATTERNS):
            # Don't flag secure functions
            if 'secure' not in self.current_function.lower():
                # Analyze the selfdestruct for security issues
                func_info = {
                    'function': self.current_function,
                    'line': ctx.start.line,
                    'call_text': call_text,
                    'has_access_control': self._check_function_access_control(),
                    'has_admin_check': self._check_admin_authorization(call_text_lower),
                    'public_access': self._check_public_access(),
                    'has_circuit_breaker': self._check_circuit_breaker_protection(),
                    'has_time_lock': self._check_time_lock_protection()
                }
                self.selfdestruct_functions.append(func_info)
            
    def enterPrimaryExpression(self, ctx):
        """Check primary expressions for selfdestruct calls."""
        if not self.current_function or not self.current_contract:
            return
            
        expr_text = ctx.getText()
        expr_text_lower = expr_text.lower()
        
        # Check for selfdestruct in expressions
        if 'selfdestruct' in expr_text_lower:
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
                        'has_admin_check': self._check_admin_authorization(parent_text.lower()),
                        'public_access': self._check_public_access(),
                        'has_circuit_breaker': self._check_circuit_breaker_protection(),
                        'has_time_lock': self._check_time_lock_protection()
                    }
                    self.selfdestruct_functions.append(func_info)
                
    def _check_function_access_control(self):
        """Check if current function has access control."""
        return self.has_access_control_modifiers or self.has_admin_role
        
    def _check_admin_authorization(self, call_text_lower):
        """Check if the selfdestruct call includes admin authorization."""
        # Look for admin authorization patterns in the call context
        admin_patterns = ['msg.sender==owner', 'msg.sender==admin', 'onlyowner', 'onlyadmin']
        # Also check if function has modifiers or the function is in a secure context
        has_admin_patterns = any(pattern in call_text_lower for pattern in admin_patterns)
        has_modifiers = self.has_access_control_modifiers
        has_admin_role = self.has_admin_role
        
        return has_admin_patterns or has_modifiers or has_admin_role
        
    def _check_public_access(self):
        """Check if the function with selfdestruct has public access."""
        # This is a simplified check - in practice, we'd analyze the function visibility
        # For now, we assume functions without explicit access control are potentially public
        return not self.has_access_control_modifiers
        
    def _check_circuit_breaker_protection(self):
        """Check if the contract has circuit breaker protection."""
        return self.has_circuit_breakers
        
    def _check_time_lock_protection(self):
        """Check if the contract has time lock protection."""
        return self.has_time_locks
        
    def enterRequireStatement(self, ctx):
        """Check require statements for admin authorization."""
        if not self.current_function or not self.current_contract:
            return
            
        require_text = ctx.getText()
        require_text_lower = require_text.lower()
        
        # Check for admin authorization in require statements
        if any(pattern in require_text_lower for pattern in self.ADMIN_ROLE_PATTERNS):
            # Update selfdestruct functions if they exist in current function
            for func_info in self.selfdestruct_functions:
                if func_info['function'] == self.current_function:
                    func_info['has_admin_check'] = True
                    func_info['has_access_control'] = True
                    break
                    
    def enterExpressionStatement(self, ctx):
        """Check expression statements for require calls with admin checks."""
        if not self.current_function or not self.current_contract:
            return
            
        expr_text = ctx.getText()
        expr_text_lower = expr_text.lower()
        
        # Check for require statements with admin authorization
        if 'require(' in expr_text_lower:
            if any(pattern in expr_text_lower for pattern in self.ADMIN_ROLE_PATTERNS):
                # Update selfdestruct functions if they exist in current function
                for func_info in self.selfdestruct_functions:
                    if func_info['function'] == self.current_function:
                        func_info['has_admin_check'] = True
                        func_info['has_access_control'] = True
                        break
                        
    def get_violations(self):
        """Return list of detected violations."""
        return self.violations
