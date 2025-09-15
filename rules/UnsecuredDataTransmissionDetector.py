from antlr4 import *
from SolidityParserListener import SolidityParserListener

class UnsecuredDataTransmissionDetector(SolidityParserListener):
    """
    Detector for SCWE-021: Unsecured Data Transmission
    Rule Code: 021
    
    Detects unsecured data transmission patterns including:
    - Functions that transmit sensitive data without encryption
    - Missing encryption for sensitive information
    - Unsecured data handling patterns
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.current_function = None
        self.processed_lines = set()
        
        # Sensitive data patterns
        self.sensitive_data_patterns = [
            'private', 'secret', 'key', 'password', 'credential', 'token',
            'address', 'wallet', 'seed', 'mnemonic', 'signature', 'hash',
            'password', 'pin', 'ssn', 'social', 'security', 'personal',
            'confidential', 'sensitive', 'encrypted', 'decrypted'
        ]
        
        # Data transmission patterns
        self.transmission_patterns = [
            'transmit', 'send', 'transfer', 'broadcast', 'emit', 'log',
            'return', 'output', 'export', 'share', 'publish', 'post',
            'call', 'delegatecall', 'staticcall', 'external', 'public'
        ]
        
        # Encryption patterns
        self.encryption_patterns = [
            'encrypt', 'decrypt', 'cipher', 'encode', 'decode',
            'hash', 'keccak256', 'sha256', 'ripemd160', 'ecrecover',
            'encrypted', 'encryptedData', 'encrypted_data', 'ciphertext',
            'plaintext', 'encryption', 'decryption'
        ]
        
        # Secure transmission patterns
        self.secure_patterns = [
            'encrypted', 'encrypt', 'hash', 'keccak256', 'sha256',
            'secure', 'protected', 'encryptedData', 'encrypted_data',
            'ciphertext', 'encryption', 'decryption'
        ]
        
        # Functions that typically handle sensitive data
        self.sensitive_functions = [
            'transmit', 'send', 'transfer', 'broadcast', 'emit', 'log',
            'return', 'output', 'export', 'share', 'publish', 'post',
            'call', 'delegatecall', 'staticcall', 'process', 'handle',
            'store', 'save', 'write', 'set', 'update', 'modify'
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
    
    def exitFunctionDefinition(self, ctx):
        """Clear function context when exiting."""
        self.current_function = None
    
    def enterExpressionStatement(self, ctx):
        """Check for unsecured data transmission patterns in function bodies."""
        if not self.current_function or not self.current_contract:
            return
            
        expr_text = ctx.getText()
        line_number = ctx.start.line
        
        # Skip if already processed this line
        if line_number in self.processed_lines:
            return
        
        # Check if this function handles sensitive data
        if self._is_sensitive_function():
            # Check for transmission patterns without encryption
            if self._has_transmission_pattern(expr_text) and not self._has_encryption_pattern(expr_text):
                violation = {
                    'type': 'SCWE-021',
                    'contract': self.current_contract,
                    'function': self.current_function,
                    'line': line_number,
                    'message': f"Function '{self.current_function}' transmits data without encryption"
                }
                self.violations.append(violation)
                self.processed_lines.add(line_number)
    
    def enterVariableDeclarationStatement(self, ctx):
        """Check for unsecured data transmission in variable declarations."""
        if not self.current_function or not self.current_contract:
            return
            
        var_text = ctx.getText()
        line_number = ctx.start.line
        
        # Skip if already processed this line
        if line_number in self.processed_lines:
            return
        
        # Check for sensitive data without encryption
        if self._is_sensitive_function():
            if self._has_sensitive_data(var_text) and not self._has_encryption_pattern(var_text):
                violation = {
                    'type': 'SCWE-021',
                    'contract': self.current_contract,
                    'function': self.current_function,
                    'line': line_number,
                    'message': f"Function '{self.current_function}' handles sensitive data without encryption"
                }
                self.violations.append(violation)
                self.processed_lines.add(line_number)
    
    def _is_sensitive_function(self):
        """Check if the current function is likely to handle sensitive data."""
        if not self.current_function:
            return False
        
        func_lower = self.current_function.lower()
        return any(pattern.lower() in func_lower for pattern in self.sensitive_functions)
    
    def _has_transmission_pattern(self, text):
        """Check if the text contains data transmission patterns."""
        text_lower = text.lower()
        return any(pattern.lower() in text_lower for pattern in self.transmission_patterns)
    
    def _has_encryption_pattern(self, text):
        """Check if the text contains encryption patterns."""
        text_lower = text.lower()
        return any(pattern.lower() in text_lower for pattern in self.encryption_patterns)
    
    def _has_sensitive_data(self, text):
        """Check if the text contains sensitive data patterns."""
        text_lower = text.lower()
        return any(pattern.lower() in text_lower for pattern in self.sensitive_data_patterns)
    
    def get_violations(self):
        """Return all detected violations."""
        return self.violations
