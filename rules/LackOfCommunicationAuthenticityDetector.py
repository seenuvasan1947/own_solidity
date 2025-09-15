from antlr4 import *
from SolidityParserListener import SolidityParserListener

class LackOfCommunicationAuthenticityDetector(SolidityParserListener):
    """
    Detector for SCWE-023: Lack of Communication Authenticity
    Rule Code: 023
    
    Detects lack of communication authenticity including:
    - Functions that process messages without authenticity verification
    - Missing signature validation
    - Absence of message integrity checks
    - Lack of sender verification
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.current_function = None
        self.processed_lines = set()
        self.function_has_authenticity = {}
        
        # Message processing patterns
        self.message_patterns = [
            'processMessage', 'handleMessage', 'executeMessage', 'verifyMessage',
            'processTransaction', 'handleTransaction', 'executeTransaction',
            'process', 'handle', 'execute', 'verify', 'validate'
        ]
        
        # Authenticity verification patterns
        self.authenticity_patterns = [
            'signature', 'sign', 'signed', 'signer', 'ecrecover', 'recover',
            'authenticity', 'authentic', 'verify', 'validation', 'integrity',
            'hash', 'keccak256', 'sha256', 'messageHash', 'transactionHash'
        ]
        
        # Secure authenticity patterns
        self.secure_patterns = [
            'require(signer ==', 'require(signer!=', 'require(signer !=',
            'assert(signer ==', 'assert(signer!=', 'assert(signer !=',
            'if (signer ==', 'if (signer!=', 'if (signer !=',
            'require(ecrecover', 'assert(ecrecover',
            'require(signer==', 'require(signer!=', 'require(signer!=',
            'assert(signer==', 'assert(signer!=', 'assert(signer!=',
            'if (signer==', 'if (signer!=', 'if (signer!=',
            'require(keccak256', 'assert(keccak256',
            'require(sha256', 'assert(sha256',
            'require(messageHash', 'assert(messageHash',
            'require(transactionHash', 'assert(transactionHash'
        ]
        
        # Functions that typically need authenticity verification
        self.authenticity_sensitive_functions = [
            'process', 'handle', 'execute', 'verify', 'validate',
            'message', 'transaction', 'action', 'operation', 'command'
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
        
        # Initialize authenticity tracking for this function
        if self.current_function:
            self.function_has_authenticity[self.current_function] = False
    
    def exitFunctionDefinition(self, ctx):
        """Analyze function for authenticity verification when exiting."""
        if not self.current_contract or not self.current_function:
            return
        
        # Check if this function processes messages and needs authenticity verification
        if self._is_authenticity_sensitive_function():
            # Check if the function has authenticity verification
            if not self.function_has_authenticity.get(self.current_function, False):
                violation = {
                    'type': 'SCWE-023',
                    'contract': self.current_contract,
                    'function': self.current_function,
                    'line': ctx.start.line,
                    'message': f"Function '{self.current_function}' processes messages without authenticity verification"
                }
                self.violations.append(violation)
        
        self.current_function = None
    
    def enterExpressionStatement(self, ctx):
        """Check for authenticity verification patterns in function bodies."""
        if not self.current_function or not self.current_contract:
            return
            
        expr_text = ctx.getText()
        
        # Check for authenticity verification patterns
        if any(pattern in expr_text for pattern in self.secure_patterns):
            self.function_has_authenticity[self.current_function] = True
    
    def enterVariableDeclarationStatement(self, ctx):
        """Check for authenticity verification variables in function bodies."""
        if not self.current_function or not self.current_contract:
            return
            
        var_text = ctx.getText()
        
        # Check for authenticity verification variable declarations
        if any(pattern in var_text for pattern in self.authenticity_patterns):
            self.function_has_authenticity[self.current_function] = True
    
    def _is_authenticity_sensitive_function(self):
        """Check if the current function is likely to process messages and need authenticity verification."""
        if not self.current_function:
            return False
        
        func_lower = self.current_function.lower()
        return any(pattern.lower() in func_lower for pattern in self.authenticity_sensitive_functions)
    
    def get_violations(self):
        """Return all detected violations."""
        return self.violations
