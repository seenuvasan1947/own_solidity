from antlr4 import *
from SolidityParserListener import SolidityParserListener

class DependencyOnBlockGasLimitDetector(SolidityParserListener):
    """
    Detector for SCWE-032: Dependency on Block Gas Limit
    Rule Code: 032
    
    Detects dependency on block gas limit including:
    - Unbounded loops
    - Large array operations
    - Gas-intensive operations without limits
    - Missing batch processing mechanisms
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.current_function = None
        self.processed_lines = set()
        
        # Gas-intensive patterns
        self.gas_intensive_patterns = [
            'for (', 'while (', 'do {', 'loop', 'iterate',
            'push(', 'pop(', 'array', 'Array', 'mapping',
            'storage', 'Storage', 'memory', 'Memory'
        ]
        
        # Unbounded loop patterns
        self.unbounded_patterns = [
            'for (uint i = 0; i <', 'for (uint i = 0; i<',
            'while (true)', 'while(true)', 'do {', 'loop',
            'unbounded', 'infinite', 'endless'
        ]
        
        # Safe patterns
        self.safe_patterns = [
            'require(i <', 'assert(i <', 'if (i <',
            'require(end <=', 'assert(end <=', 'if (end <=',
            'require(limit', 'assert(limit', 'if (limit',
            'require(max', 'assert(max', 'if (max',
            'require(batch', 'assert(batch', 'if (batch',
            'chunk', 'Chunk', 'batch', 'Batch', 'limit', 'Limit'
        ]
        
        # Gas-intensive functions
        self.gas_functions = [
            'process', 'handle', 'execute', 'batch', 'chunk',
            'iterate', 'loop', 'array', 'list', 'collection'
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
        """Check for gas-intensive operations in function bodies."""
        if not self.current_function or not self.current_contract:
            return
            
        expr_text = ctx.getText()
        line_number = ctx.start.line
        
        # Skip if already processed this line
        if line_number in self.processed_lines:
            return
        
        # Check for gas-intensive operations
        if self._is_gas_intensive_function():
            if self._has_unbounded_operations(expr_text) and not self._has_safe_limits(expr_text):
                violation = {
                    'type': 'SCWE-032',
                    'contract': self.current_contract,
                    'function': self.current_function,
                    'line': line_number,
                    'message': f"Function '{self.current_function}' has gas-intensive operations without limits"
                }
                self.violations.append(violation)
                self.processed_lines.add(line_number)
    
    def enterVariableDeclarationStatement(self, ctx):
        """Check for gas-intensive operations in variable declarations."""
        if not self.current_function or not self.current_contract:
            return
            
        var_text = ctx.getText()
        line_number = ctx.start.line
        
        # Skip if already processed this line
        if line_number in self.processed_lines:
            return
        
        # Check for gas-intensive operations
        if self._is_gas_intensive_function():
            if self._has_unbounded_operations(var_text) and not self._has_safe_limits(var_text):
                violation = {
                    'type': 'SCWE-032',
                    'contract': self.current_contract,
                    'function': self.current_function,
                    'line': line_number,
                    'message': f"Function '{self.current_function}' has gas-intensive operations without limits"
                }
                self.violations.append(violation)
                self.processed_lines.add(line_number)
    
    def _is_gas_intensive_function(self):
        """Check if the current function is likely to be gas-intensive."""
        if not self.current_function:
            return False
        
        func_lower = self.current_function.lower()
        return any(pattern.lower() in func_lower for pattern in self.gas_functions)
    
    def _has_unbounded_operations(self, text):
        """Check if the text contains unbounded operations."""
        text_lower = text.lower()
        return any(pattern.lower() in text_lower for pattern in self.unbounded_patterns)
    
    def _has_safe_limits(self, text):
        """Check if the text contains safe limits."""
        text_lower = text.lower()
        return any(pattern.lower() in text_lower for pattern in self.safe_patterns)
    
    def get_violations(self):
        """Return all detected violations."""
        return self.violations
