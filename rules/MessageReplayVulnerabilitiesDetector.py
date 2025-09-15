from antlr4 import *
from SolidityParserListener import SolidityParserListener

class MessageReplayVulnerabilitiesDetector(SolidityParserListener):
    """
    Detector for SCWE-022: Message Replay Vulnerabilities
    Rule Code: 022
    
    Detects message replay vulnerabilities including:
    - Functions that process messages without replay protection
    - Missing nonce mechanisms
    - Absence of timestamp validation
    - Lack of message uniqueness checks
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.current_function = None
        self.processed_lines = set()
        self.function_has_replay_protection = {}
        
        # Message processing patterns
        self.message_patterns = [
            'processMessage', 'handleMessage', 'executeMessage', 'verifyMessage',
            'processTransaction', 'handleTransaction', 'executeTransaction',
            'process', 'handle', 'execute', 'verify', 'validate'
        ]
        
        # Replay protection patterns
        self.replay_protection_patterns = [
            'nonce', 'usedMessages', 'usedTransactions', 'processedMessages',
            'messageHash', 'transactionHash', 'replay', 'replayProtection',
            'usedNonces', 'nonceUsed', 'alreadyUsed', 'alreadyProcessed',
            'timestamp', 'expiry', 'expire', 'validUntil', 'validFor'
        ]
        
        # Secure replay protection patterns
        self.secure_patterns = [
            'require(!usedMessages', 'require(!usedTransactions',
            'require(!processedMessages', 'require(!usedNonces',
            'require(!nonceUsed', 'require(!alreadyUsed',
            'require(!alreadyProcessed', 'require(block.timestamp',
            'require(timestamp', 'require(expiry', 'require(validUntil',
            'require(validFor', 'usedMessages[', 'usedTransactions[',
            'processedMessages[', 'usedNonces[', 'nonceUsed[',
            'alreadyUsed[', 'alreadyProcessed['
        ]
        
        # Functions that typically need replay protection
        self.replay_sensitive_functions = [
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
        
        # Initialize replay protection tracking for this function
        if self.current_function:
            self.function_has_replay_protection[self.current_function] = False
    
    def exitFunctionDefinition(self, ctx):
        """Analyze function for replay protection when exiting."""
        if not self.current_contract or not self.current_function:
            return
        
        # Check if this function processes messages and needs replay protection
        if self._is_replay_sensitive_function():
            # Check if the function has replay protection
            if not self.function_has_replay_protection.get(self.current_function, False):
                violation = {
                    'type': 'SCWE-022',
                    'contract': self.current_contract,
                    'function': self.current_function,
                    'line': ctx.start.line,
                    'message': f"Function '{self.current_function}' processes messages without replay protection"
                }
                self.violations.append(violation)
        
        self.current_function = None
    
    def enterExpressionStatement(self, ctx):
        """Check for replay protection patterns in function bodies."""
        if not self.current_function or not self.current_contract:
            return
            
        expr_text = ctx.getText()
        
        # Check for replay protection patterns
        if any(pattern in expr_text for pattern in self.secure_patterns):
            self.function_has_replay_protection[self.current_function] = True
    
    def enterVariableDeclarationStatement(self, ctx):
        """Check for replay protection variables in function bodies."""
        if not self.current_function or not self.current_contract:
            return
            
        var_text = ctx.getText()
        
        # Check for replay protection variable declarations
        if any(pattern in var_text for pattern in self.replay_protection_patterns):
            self.function_has_replay_protection[self.current_function] = True
    
    def _is_replay_sensitive_function(self):
        """Check if the current function is likely to process messages and need replay protection."""
        if not self.current_function:
            return False
        
        func_lower = self.current_function.lower()
        return any(pattern.lower() in func_lower for pattern in self.replay_sensitive_functions)
    
    def get_violations(self):
        """Return all detected violations."""
        return self.violations
