from antlr4 import *
from SolidityParserListener import SolidityParserListener

class WeakRandomnessSourcesDetector(SolidityParserListener):
    """
    Detector for SCWE-024: Weak Randomness Sources
    Rule Code: 024
    
    Detects weak randomness sources including:
    - Use of block.timestamp for randomness
    - Use of block.difficulty for randomness
    - Use of block.number for randomness
    - Use of blockhash for randomness
    - Other predictable randomness sources
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.current_function = None
        self.processed_lines = set()
        
        # Weak randomness patterns
        self.weak_randomness_patterns = [
            'block.timestamp', 'block.difficulty', 'block.number', 'blockhash',
            'now', 'block.coinbase', 'block.gaslimit', 'block.chainid',
            'msg.sender', 'tx.origin', 'tx.gasprice', 'tx.origin'
        ]
        
        # Secure randomness patterns
        self.secure_randomness_patterns = [
            'chainlink', 'vrf', 'VRF', 'randomness', 'oracle',
            'external', 'api', 'entropy', 'secure', 'cryptographic'
        ]
        
        # Randomness function patterns
        self.randomness_functions = [
            'random', 'generate', 'pick', 'select', 'choose', 'shuffle',
            'randomNumber', 'randomValue', 'randomSeed', 'randomHash',
            'generateRandom', 'getRandom', 'createRandom', 'randomize'
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
        """Check for weak randomness patterns in function bodies."""
        if not self.current_function or not self.current_contract:
            return
            
        expr_text = ctx.getText()
        line_number = ctx.start.line
        
        # Skip if already processed this line
        if line_number in self.processed_lines:
            return
        
        # Check if this function generates randomness
        if self._is_randomness_function():
            # Check for weak randomness patterns
            if self._has_weak_randomness(expr_text) and not self._has_secure_randomness(expr_text):
                violation = {
                    'type': 'SCWE-024',
                    'contract': self.current_contract,
                    'function': self.current_function,
                    'line': line_number,
                    'message': f"Function '{self.current_function}' uses weak randomness sources"
                }
                self.violations.append(violation)
                self.processed_lines.add(line_number)
    
    def enterVariableDeclarationStatement(self, ctx):
        """Check for weak randomness patterns in variable declarations."""
        if not self.current_function or not self.current_contract:
            return
            
        var_text = ctx.getText()
        line_number = ctx.start.line
        
        # Skip if already processed this line
        if line_number in self.processed_lines:
            return
        
        # Check if this function generates randomness
        if self._is_randomness_function():
            # Check for weak randomness patterns
            if self._has_weak_randomness(var_text) and not self._has_secure_randomness(var_text):
                violation = {
                    'type': 'SCWE-024',
                    'contract': self.current_contract,
                    'function': self.current_function,
                    'line': line_number,
                    'message': f"Function '{self.current_function}' uses weak randomness sources"
                }
                self.violations.append(violation)
                self.processed_lines.add(line_number)
    
    def _is_randomness_function(self):
        """Check if the current function is likely to generate randomness."""
        if not self.current_function:
            return False
        
        func_lower = self.current_function.lower()
        return any(pattern.lower() in func_lower for pattern in self.randomness_functions)
    
    def _has_weak_randomness(self, text):
        """Check if the text contains weak randomness patterns."""
        text_lower = text.lower()
        return any(pattern.lower() in text_lower for pattern in self.weak_randomness_patterns)
    
    def _has_secure_randomness(self, text):
        """Check if the text contains secure randomness patterns."""
        text_lower = text.lower()
        return any(pattern.lower() in text_lower for pattern in self.secure_randomness_patterns)
    
    def get_violations(self):
        """Return all detected violations."""
        return self.violations
