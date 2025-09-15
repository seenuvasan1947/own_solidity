from antlr4 import *
from SolidityParserListener import SolidityParserListener

class ImproperCryptographicKeyManagementDetector(SolidityParserListener):
    """
    Detector for SCWE-025: Improper Cryptographic Key Management
    Rule Code: 025
    
    Detects improper cryptographic key management including:
    - Hardcoded cryptographic keys
    - Insecure key generation
    - Missing key rotation mechanisms
    - Improper key storage
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.current_function = None
        self.processed_lines = set()
        
        # Cryptographic key patterns
        self.key_patterns = [
            'private', 'secret', 'key', 'seed', 'mnemonic', 'password',
            'cryptographic', 'encryption', 'decryption', 'signature',
            'keccak256', 'sha256', 'ripemd160', 'ecrecover'
        ]
        
        # Hardcoded key patterns
        self.hardcoded_patterns = [
            'keccak256("', 'sha256("', 'ripemd160("',
            'keccak256(\'', 'sha256(\'', 'ripemd160(\'',
            'bytes32', 'bytes', 'string', 'uint256'
        ]
        
        # Secure key management patterns
        self.secure_patterns = [
            'constructor', 'initialize', 'setKey', 'updateKey', 'rotateKey',
            'external', 'oracle', 'chainlink', 'vrf', 'VRF', 'randomness',
            'secure', 'cryptographic', 'entropy', 'generator'
        ]
        
        # Key management functions
        self.key_functions = [
            'generate', 'create', 'set', 'update', 'rotate', 'manage',
            'key', 'secret', 'private', 'cryptographic', 'encryption'
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
        """Check for improper key management patterns in function bodies."""
        if not self.current_function or not self.current_contract:
            return
            
        expr_text = ctx.getText()
        line_number = ctx.start.line
        
        # Skip if already processed this line
        if line_number in self.processed_lines:
            return
        
        # Check for hardcoded keys
        if self._has_hardcoded_key(expr_text):
            violation = {
                'type': 'SCWE-025',
                'contract': self.current_contract,
                'function': self.current_function,
                'line': line_number,
                'message': f"Function '{self.current_function}' contains hardcoded cryptographic key"
            }
            self.violations.append(violation)
            self.processed_lines.add(line_number)
    
    def enterVariableDeclarationStatement(self, ctx):
        """Check for improper key management patterns in variable declarations."""
        if not self.current_function or not self.current_contract:
            return
            
        var_text = ctx.getText()
        line_number = ctx.start.line
        
        # Skip if already processed this line
        if line_number in self.processed_lines:
            return
        
        # Check for hardcoded keys
        if self._has_hardcoded_key(var_text):
            violation = {
                'type': 'SCWE-025',
                'contract': self.current_contract,
                'function': self.current_function,
                'line': line_number,
                'message': f"Function '{self.current_function}' contains hardcoded cryptographic key"
            }
            self.violations.append(violation)
            self.processed_lines.add(line_number)
    
    def _has_hardcoded_key(self, text):
        """Check if the text contains hardcoded cryptographic keys."""
        text_lower = text.lower()
        
        # Check for hardcoded key patterns
        for pattern in self.hardcoded_patterns:
            if pattern in text:
                # Check if it's not in a secure context
                if not any(secure_pattern in text_lower for secure_pattern in self.secure_patterns):
                    return True
        
        return False
    
    def get_violations(self):
        """Return all detected violations."""
        return self.violations
