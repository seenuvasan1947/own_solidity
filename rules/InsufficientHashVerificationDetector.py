from antlr4 import *
from SolidityParserListener import SolidityParserListener

class InsufficientHashVerificationDetector(SolidityParserListener):
    """
    Detector for SCWE-026: Insufficient Hash Verification
    Rule Code: 026
    
    Detects insufficient hash verification including:
    - Functions that process hashes without verification
    - Missing hash validation
    - Absence of hash integrity checks
    - Lack of hash comparison
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.current_function = None
        self.processed_lines = set()
        self.function_has_hash_verification = {}
        
        # Hash processing patterns
        self.hash_patterns = [
            'hash', 'keccak256', 'sha256', 'ripemd160', 'ecrecover',
            'messageHash', 'transactionHash', 'dataHash', 'contentHash',
            'verify', 'validation', 'integrity', 'authenticity'
        ]
        
        # Hash verification patterns
        self.verification_patterns = [
            'require(keccak256', 'assert(keccak256', 'if (keccak256',
            'require(sha256', 'assert(sha256', 'if (sha256',
            'require(ripemd160', 'assert(ripemd160', 'if (ripemd160',
            'require(hash', 'assert(hash', 'if (hash',
            'require(messageHash', 'assert(messageHash', 'if (messageHash',
            'require(transactionHash', 'assert(transactionHash', 'if (transactionHash',
            'require(dataHash', 'assert(dataHash', 'if (dataHash',
            'require(contentHash', 'assert(contentHash', 'if (contentHash',
            'require(verify', 'assert(verify', 'if (verify',
            'require(validation', 'assert(validation', 'if (validation',
            'require(integrity', 'assert(integrity', 'if (integrity',
            'require(authenticity', 'assert(authenticity', 'if (authenticity'
        ]
        
        # Functions that typically process hashes
        self.hash_functions = [
            'process', 'handle', 'execute', 'verify', 'validate',
            'hash', 'message', 'transaction', 'data', 'content'
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
        
        # Initialize hash verification tracking for this function
        if self.current_function:
            self.function_has_hash_verification[self.current_function] = False
    
    def exitFunctionDefinition(self, ctx):
        """Analyze function for hash verification when exiting."""
        if not self.current_contract or not self.current_function:
            return
        
        # Check if this function processes hashes and needs verification
        if self._is_hash_function():
            # Check if the function has hash verification
            if not self.function_has_hash_verification.get(self.current_function, False):
                violation = {
                    'type': 'SCWE-026',
                    'contract': self.current_contract,
                    'function': self.current_function,
                    'line': ctx.start.line,
                    'message': f"Function '{self.current_function}' processes hashes without verification"
                }
                self.violations.append(violation)
        
        self.current_function = None
    
    def enterExpressionStatement(self, ctx):
        """Check for hash verification patterns in function bodies."""
        if not self.current_function or not self.current_contract:
            return
            
        expr_text = ctx.getText()
        
        # Check for hash verification patterns
        if any(pattern in expr_text for pattern in self.verification_patterns):
            self.function_has_hash_verification[self.current_function] = True
    
    def enterVariableDeclarationStatement(self, ctx):
        """Check for hash verification variables in function bodies."""
        if not self.current_function or not self.current_contract:
            return
            
        var_text = ctx.getText()
        
        # Check for hash verification variable declarations
        if any(pattern in var_text for pattern in self.hash_patterns):
            self.function_has_hash_verification[self.current_function] = True
    
    def _is_hash_function(self):
        """Check if the current function is likely to process hashes."""
        if not self.current_function:
            return False
        
        func_lower = self.current_function.lower()
        return any(pattern.lower() in func_lower for pattern in self.hash_functions)
    
    def get_violations(self):
        """Return all detected violations."""
        return self.violations
