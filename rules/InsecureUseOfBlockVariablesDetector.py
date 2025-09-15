from antlr4 import *
from SolidityParserListener import SolidityParserListener

class InsecureUseOfBlockVariablesDetector(SolidityParserListener):
    """
    Detector for SCWE-031: Insecure use of Block Variables
    Rule Code: 031
    
    Detects insecure use of block variables including:
    - Use of block.timestamp for critical timing
    - Use of block.number for randomness
    - Use of block.difficulty for randomness
    - Use of blockhash for randomness
    - Other insecure block variable usage
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.current_function = None
        self.processed_lines = set()
        
        # Insecure block variable patterns
        self.insecure_block_patterns = [
            'block.timestamp', 'block.number', 'block.difficulty', 'blockhash',
            'now', 'block.coinbase', 'block.gaslimit', 'block.chainid'
        ]
        
        # Secure alternatives
        self.secure_alternatives = [
            'chainlink', 'vrf', 'VRF', 'oracle', 'Oracle', 'external',
            'api', 'entropy', 'secure', 'cryptographic', 'randomness'
        ]
        
        # Critical timing functions
        self.timing_functions = [
            'deadline', 'expire', 'expiry', 'timeout', 'duration',
            'period', 'interval', 'schedule', 'timing', 'time'
        ]
        
        # Randomness functions
        self.randomness_functions = [
            'random', 'generate', 'pick', 'select', 'choose', 'shuffle',
            'lottery', 'winner', 'draw', 'entropy', 'seed'
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
        """Check for insecure block variable usage in function bodies."""
        if not self.current_function or not self.current_contract:
            return
            
        expr_text = ctx.getText()
        line_number = ctx.start.line
        
        # Skip if already processed this line
        if line_number in self.processed_lines:
            return
        
        # Check for insecure block variable usage
        if self._has_insecure_block_usage(expr_text) and not self._has_secure_alternative(expr_text):
            violation = {
                'type': 'SCWE-031',
                'contract': self.current_contract,
                'function': self.current_function,
                'line': line_number,
                'message': f"Function '{self.current_function}' uses block variables insecurely"
            }
            self.violations.append(violation)
            self.processed_lines.add(line_number)
    
    def enterVariableDeclarationStatement(self, ctx):
        """Check for insecure block variable usage in variable declarations."""
        if not self.current_function or not self.current_contract:
            return
            
        var_text = ctx.getText()
        line_number = ctx.start.line
        
        # Skip if already processed this line
        if line_number in self.processed_lines:
            return
        
        # Check for insecure block variable usage
        if self._has_insecure_block_usage(var_text) and not self._has_secure_alternative(var_text):
            violation = {
                'type': 'SCWE-031',
                'contract': self.current_contract,
                'function': self.current_function,
                'line': line_number,
                'message': f"Function '{self.current_function}' uses block variables insecurely"
            }
            self.violations.append(violation)
            self.processed_lines.add(line_number)
    
    def _has_insecure_block_usage(self, text):
        """Check if the text contains insecure block variable usage."""
        text_lower = text.lower()
        return any(pattern.lower() in text_lower for pattern in self.insecure_block_patterns)
    
    def _has_secure_alternative(self, text):
        """Check if the text contains secure alternatives."""
        text_lower = text.lower()
        return any(pattern.lower() in text_lower for pattern in self.secure_alternatives)
    
    def get_violations(self):
        """Return all detected violations."""
        return self.violations
