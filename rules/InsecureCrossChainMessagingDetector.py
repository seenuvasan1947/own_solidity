from SolidityParserListener import SolidityParserListener

class InsecureCrossChainMessagingDetector(SolidityParserListener):
    """
    Rule Code: 002
    Detects SCWE-034: Insecure Cross-Chain Messaging vulnerabilities
    
    Insecure cross-chain messaging refers to vulnerabilities that arise when communicating 
    between different blockchains. This can lead to unauthorized actions by malicious actors,
    loss of funds or data, and exploitation of vulnerabilities in cross-chain logic.
    """
    
    # Constants for cross-chain messaging patterns
    CROSS_CHAIN_FUNCTION_PATTERNS = [
        'processmessage', 'handlemessage', 'receivemessage', 'executemessage',
        'bridgemessage', 'relaymessage', 'crosschainmessage'
    ]
    
    RELAYER_PATTERNS = ['relayer', 'relay', 'bridge', 'messenger']
    SIGNATURE_PATTERNS = ['ecrecover', 'signature', 'verify', 'sign']
    REPLAY_PROTECTION_PATTERNS = ['nonce', 'processed', 'executed', 'messagehash']
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.current_function = None
        self.has_relayer_validation = False
        self.has_signature_verification = False
        self.has_replay_protection = False
        self.cross_chain_functions = []
        self.trusted_relayer_mapping = False
        self.processed_messages_mapping = False
        
    def enterContractDefinition(self, ctx):
        """Track contract definitions and reset tracking variables."""
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "UnknownContract"
        self.has_relayer_validation = False
        self.has_signature_verification = False
        self.has_replay_protection = False
        self.cross_chain_functions = []
        self.trusted_relayer_mapping = False
        self.processed_messages_mapping = False
        
    def exitContractDefinition(self, ctx):
        """Check for missing cross-chain security mechanisms at contract level."""
        if (self.current_contract and self.cross_chain_functions and 
            'secure' not in self.current_contract.lower()):
            if not self.trusted_relayer_mapping:
                self.violations.append(
                    f"SCWE-034: Contract '{self.current_contract}' handles cross-chain messages "
                    f"but lacks trusted relayer mapping for authorization control."
                )
            if not self.processed_messages_mapping:
                self.violations.append(
                    f"SCWE-034: Contract '{self.current_contract}' handles cross-chain messages "
                    f"but lacks processed messages mapping for replay protection."
                )
        self.current_contract = None
        
    def enterFunctionDefinition(self, ctx):
        """Track function definitions."""
        if not self.current_contract:
            return
            
        func_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.current_function = func_name
        
        # Check if this is a cross-chain message processing function
        func_name_lower = func_name.lower()
        if any(pattern in func_name_lower for pattern in self.CROSS_CHAIN_FUNCTION_PATTERNS):
            # Don't track secure functions as vulnerable
            if 'secure' not in func_name_lower:
                self.cross_chain_functions.append({
                    'function': func_name,
                    'line': ctx.start.line,
                    'has_relayer_check': False,
                    'has_signature_check': False,
                    'has_replay_protection': False
                })
        
    def exitFunctionDefinition(self, ctx):
        """Check cross-chain functions for security vulnerabilities."""
        if self.current_function and self.cross_chain_functions:
            # Find current function in cross_chain_functions
            current_func_info = None
            for func_info in self.cross_chain_functions:
                if func_info['function'] == self.current_function:
                    current_func_info = func_info
                    break
                    
            if current_func_info:
                # Check for missing security measures
                if not current_func_info['has_relayer_check']:
                    self.violations.append(
                        f"SCWE-034: Function '{self.current_function}' at line {current_func_info['line']} "
                        f"processes cross-chain messages without relayer authorization validation. "
                        f"Consider adding trusted relayer checks."
                    )
                    
                if not current_func_info['has_signature_check']:
                    self.violations.append(
                        f"SCWE-034: Function '{self.current_function}' at line {current_func_info['line']} "
                        f"processes cross-chain messages without signature verification. "
                        f"Consider adding ecrecover or signature validation."
                    )
                    
                if not current_func_info['has_replay_protection']:
                    self.violations.append(
                        f"SCWE-034: Function '{self.current_function}' at line {current_func_info['line']} "
                        f"processes cross-chain messages without replay protection. "
                        f"Consider tracking processed message hashes."
                    )
        
        self.current_function = None
        
    def enterStateVariableDeclaration(self, ctx):
        """Check for security-related state variables."""
        if not self.current_contract:
            return
            
        var_name = ctx.identifier().getText() if ctx.identifier() else ""
        var_name_lower = var_name.lower()
        
        # Check for trusted relayer mapping
        if any(pattern in var_name_lower for pattern in self.RELAYER_PATTERNS) and 'mapping' in ctx.getText().lower():
            self.trusted_relayer_mapping = True
            
        # Check for processed messages mapping
        if any(pattern in var_name_lower for pattern in self.REPLAY_PROTECTION_PATTERNS) and 'mapping' in ctx.getText().lower():
            self.processed_messages_mapping = True
            
    def enterRequireStatement(self, ctx):
        """Check require statements for security validations."""
        if not self.current_function or not self.current_contract:
            return
            
        require_text = ctx.getText()
        require_text_lower = require_text.lower()
        
        # Update current function info if it's a cross-chain function
        self._update_function_security_checks(require_text_lower)
        
    def enterExpressionStatement(self, ctx):
        """Check expression statements for require calls and security checks."""
        if not self.current_function or not self.current_contract:
            return
            
        expr_text = ctx.getText()
        expr_text_lower = expr_text.lower()
        
        # Check for require statements
        if 'require(' in expr_text_lower:
            self._update_function_security_checks(expr_text_lower)
            
        # Check for ecrecover calls
        if 'ecrecover(' in expr_text_lower:
            self._mark_signature_verification()
            
    def enterIfStatement(self, ctx):
        """Check if statements for security validations."""
        if not self.current_function or not self.current_contract:
            return
            
        if_text = ctx.getText()
        if_text_lower = if_text.lower()
        
        self._update_function_security_checks(if_text_lower)
        
    def enterFunctionCall(self, ctx):
        """Check function calls for security-related operations."""
        if not self.current_function or not self.current_contract:
            return
            
        call_text = ctx.getText()
        call_text_lower = call_text.lower()
        
        # Check for ecrecover calls
        if 'ecrecover(' in call_text_lower:
            self._mark_signature_verification()
            
        # Check for signature verification patterns
        if any(pattern in call_text_lower for pattern in self.SIGNATURE_PATTERNS):
            self._mark_signature_verification()
            
    def enterAssignment(self, ctx):
        """Check assignments for replay protection mechanisms."""
        if not self.current_function or not self.current_contract:
            return
            
        assignment_text = ctx.getText()
        assignment_text_lower = assignment_text.lower()
        
        # Check for processed messages assignment
        if any(pattern in assignment_text_lower for pattern in self.REPLAY_PROTECTION_PATTERNS):
            self._mark_replay_protection()
            
    def _update_function_security_checks(self, text_lower):
        """Update security check flags for current cross-chain function."""
        if not self.cross_chain_functions:
            return
            
        # Find current function in cross_chain_functions
        for func_info in self.cross_chain_functions:
            if func_info['function'] == self.current_function:
                # Check for relayer validation
                if any(pattern in text_lower for pattern in self.RELAYER_PATTERNS):
                    func_info['has_relayer_check'] = True
                    
                # Check for signature verification
                if any(pattern in text_lower for pattern in self.SIGNATURE_PATTERNS):
                    func_info['has_signature_check'] = True
                    
                # Check for replay protection
                if any(pattern in text_lower for pattern in self.REPLAY_PROTECTION_PATTERNS):
                    func_info['has_replay_protection'] = True
                break
                
    def _mark_signature_verification(self):
        """Mark that signature verification is present in current function."""
        if not self.cross_chain_functions:
            return
            
        for func_info in self.cross_chain_functions:
            if func_info['function'] == self.current_function:
                func_info['has_signature_check'] = True
                break
                
    def _mark_replay_protection(self):
        """Mark that replay protection is present in current function."""
        if not self.cross_chain_functions:
            return
            
        for func_info in self.cross_chain_functions:
            if func_info['function'] == self.current_function:
                func_info['has_replay_protection'] = True
                break
                
    def get_violations(self):
        """Return list of detected violations."""
        return self.violations
