from antlr4 import *
from SolidityParserListener import SolidityParserListener

class VulnerableCryptographicAlgorithmsDetector(SolidityParserListener):
    """
    Detector for SCWE-027: Vulnerable Cryptographic Algorithms
    Rule Code: 027
    
    Detects vulnerable cryptographic algorithms including:
    - Use of MD5 (deprecated and insecure)
    - Use of SHA-1 (deprecated and insecure)
    - Use of other weak cryptographic algorithms
    - Missing use of secure algorithms like Keccak-256
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.current_function = None
        self.processed_lines = set()
        
        # Vulnerable cryptographic algorithms
        self.vulnerable_algorithms = [
            'md5', 'MD5', 'sha1', 'SHA1', 'sha-1', 'SHA-1',
            'ripemd128', 'RIPEMD128', 'ripemd160', 'RIPEMD160',
            'des', 'DES', 'rc4', 'RC4', 'rc2', 'RC2'
        ]
        
        # Secure cryptographic algorithms
        self.secure_algorithms = [
            'keccak256', 'Keccak256', 'KECCAK256',
            'sha256', 'SHA256', 'sha-256', 'SHA-256',
            'sha3', 'SHA3', 'sha-3', 'SHA-3',
            'blake2b', 'BLAKE2b', 'blake2s', 'BLAKE2s'
        ]
        
        # Cryptographic function patterns
        self.crypto_functions = [
            'hash', 'encrypt', 'decrypt', 'sign', 'verify',
            'digest', 'checksum', 'fingerprint', 'cryptographic'
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
        """Check for vulnerable cryptographic algorithms in function bodies."""
        if not self.current_function or not self.current_contract:
            return
            
        expr_text = ctx.getText()
        line_number = ctx.start.line
        
        # Skip if already processed this line
        if line_number in self.processed_lines:
            return
        
        # Check for vulnerable algorithms
        if self._has_vulnerable_algorithm(expr_text):
            violation = {
                'type': 'SCWE-027',
                'contract': self.current_contract,
                'function': self.current_function,
                'line': line_number,
                'message': f"Function '{self.current_function}' uses vulnerable cryptographic algorithm"
            }
            self.violations.append(violation)
            self.processed_lines.add(line_number)
    
    def enterVariableDeclarationStatement(self, ctx):
        """Check for vulnerable cryptographic algorithms in variable declarations."""
        if not self.current_function or not self.current_contract:
            return
            
        var_text = ctx.getText()
        line_number = ctx.start.line
        
        # Skip if already processed this line
        if line_number in self.processed_lines:
            return
        
        # Check for vulnerable algorithms
        if self._has_vulnerable_algorithm(var_text):
            violation = {
                'type': 'SCWE-027',
                'contract': self.current_contract,
                'function': self.current_function,
                'line': line_number,
                'message': f"Function '{self.current_function}' uses vulnerable cryptographic algorithm"
            }
            self.violations.append(violation)
            self.processed_lines.add(line_number)
    
    def _has_vulnerable_algorithm(self, text):
        """Check if the text contains vulnerable cryptographic algorithms."""
        text_lower = text.lower()
        return any(algorithm.lower() in text_lower for algorithm in self.vulnerable_algorithms)
    
    def get_violations(self):
        """Return all detected violations."""
        return self.violations
