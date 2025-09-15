from antlr4 import *
from SolidityParserListener import SolidityParserListener

class InsecureSignatureVerificationDetector(SolidityParserListener):
    """
    Detector for SCWE-019: Insecure Signature Verification
    Rule Code: 019
    
    Detects insecure signature verification patterns including:
    - Missing signature validation
    - Improper ecrecover usage
    - Missing require statements after signature verification
    - Weak signature verification patterns
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.current_function = None
        self.processed_lines = set()
        self.function_has_validation = {}
        
        # Signature verification patterns
        self.signature_patterns = [
            'ecrecover', 'recoverSigner', 'verifySignature', 'checkSignature',
            'validateSignature', 'signatureVerification'
        ]
        
        # Secure signature verification patterns
        self.secure_patterns = [
            'require(signer ==', 'require(signer!=', 'require(signer !=',
            'assert(signer ==', 'assert(signer!=', 'assert(signer !=',
            'if (signer ==', 'if (signer!=', 'if (signer !=',
            'require(ecrecover', 'assert(ecrecover',
            'require(signer==', 'require(signer!=', 'require(signer!=',
            'assert(signer==', 'assert(signer!=', 'assert(signer!=',
            'if (signer==', 'if (signer!=', 'if (signer!=',
            'require(ecrecover', 'assert(ecrecover',
            'require(signer==owner', 'require(signer==admin',
            'require(signer!=address(0)', 'require(signer!=address(0)',
            'assert(signer==owner', 'assert(signer==admin',
            'assert(signer!=address(0)', 'assert(signer!=address(0)',
            'if (signer==owner', 'if (signer==admin',
            'if (signer!=address(0)', 'if (signer!=address(0)'
        ]
        
        # Function names that typically use signature verification
        self.signature_functions = [
            'execute', 'process', 'verify', 'validate', 'check', 'confirm',
            'authorize', 'permit', 'approve', 'sign', 'executeTransaction',
            'processTransaction', 'verifyTransaction', 'validateTransaction'
        ]
    
    def enterContractDefinition(self, ctx):
        """Track contract definitions."""
        if ctx.identifier():
            self.current_contract = ctx.identifier().getText()
        else:
            self.current_contract = "UnknownContract"
    
    def exitContractDefinition(self, ctx):
        """Clear contract context when exiting."""
        self.current_contract = None
    
    def enterFunctionDefinition(self, ctx):
        """Track function definitions."""
        if not self.current_contract:
            return
            
        if ctx.identifier():
            self.current_function = ctx.identifier().getText()
        else:
            self.current_function = "unknown"
        
        # Initialize validation tracking for this function
        if self.current_function:
            self.function_has_validation[self.current_function] = False
    
    def exitFunctionDefinition(self, ctx):
        """Analyze function for signature verification when exiting."""
        if not self.current_contract or not self.current_function:
            return
        
        # Check if this function uses signature verification
        if self._is_signature_function():
            # Check if there's proper validation
            if not self.function_has_validation.get(self.current_function, False):
                violation = {
                    'type': 'SCWE-019',
                    'contract': self.current_contract,
                    'function': self.current_function,
                    'line': ctx.start.line,
                    'message': f"Function '{self.current_function}' uses signature verification without proper validation"
                }
                self.violations.append(violation)
        
        self.current_function = None
    
    def enterExpressionStatement(self, ctx):
        """Check for signature verification patterns in function bodies."""
        if not self.current_function or not self.current_contract:
            return
            
        expr_text = ctx.getText()
        
        # Check for ecrecover usage
        if 'ecrecover' in expr_text:
            # Check if there's proper validation
            if self._has_secure_validation(expr_text):
                self.function_has_validation[self.current_function] = True
    
    def enterVariableDeclarationStatement(self, ctx):
        """Check for signature verification in variable declarations."""
        if not self.current_function or not self.current_contract:
            return
            
        var_text = ctx.getText()
        
        # Check for ecrecover in variable assignment
        if 'ecrecover' in var_text:
            # Check if there's proper validation
            if self._has_secure_validation(var_text):
                self.function_has_validation[self.current_function] = True
    
    def _is_signature_function(self):
        """Check if the current function is likely to use signature verification."""
        if not self.current_function:
            return False
        
        func_lower = self.current_function.lower()
        return any(pattern.lower() in func_lower for pattern in self.signature_functions)
    
    def _has_secure_validation(self, text):
        """Check if the text contains secure signature validation patterns."""
        text_lower = text.lower()
        return any(pattern.lower() in text_lower for pattern in self.secure_patterns)
    
    def get_violations(self):
        """Return all detected violations."""
        return self.violations
