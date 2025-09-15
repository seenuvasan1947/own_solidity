from antlr4 import *
from SolidityParserListener import SolidityParserListener

class AbsenceOfTimeLockedFunctionsDetector(SolidityParserListener):
    """
    Detector for SCWE-020: Absence of Time-Locked Functions
    Rule Code: 020
    
    Detects critical functions that lack time-lock mechanisms including:
    - Functions that should have time delays but don't
    - Missing time-lock patterns for critical operations
    - Absence of time-based restrictions
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.current_function = None
        self.processed_lines = set()
        
        # Critical function patterns that should have time locks
        self.critical_functions = [
            'withdraw', 'transfer', 'mint', 'burn', 'upgrade', 'set', 'update',
            'change', 'modify', 'configure', 'emergency', 'pause', 'unpause',
            'admin', 'owner', 'governance', 'treasury', 'funds', 'tokens',
            'destroy', 'kill', 'selfdestruct', 'approve', 'revoke', 'grant',
            'remove', 'delete', 'reset', 'initialize', 'finalize'
        ]
        
        # Time-lock patterns
        self.timelock_patterns = [
            'timelock', 'timeLock', 'time_lock', 'delay', 'wait',
            'block.timestamp', 'block.number', 'now', 'time',
            'lastTime', 'last_time', 'lastExecution', 'last_execution',
            'executionTime', 'execution_time', 'lockTime', 'lock_time',
            'unlockTime', 'unlock_time', 'cooldown', 'cooldownPeriod',
            'cooldown_period', 'waitingPeriod', 'waiting_period'
        ]
        
        # Time comparison patterns
        self.time_comparison_patterns = [
            '>=', '>', 'block.timestamp >=', 'block.number >=',
            'now >=', 'block.timestamp >', 'block.number >',
            'now >', 'require(block.timestamp', 'require(block.number',
            'require(now', 'assert(block.timestamp', 'assert(block.number',
            'assert(now', 'if (block.timestamp', 'if (block.number',
            'if (now'
        ]
        
        # Functions that typically don't need time locks
        self.public_functions = [
            'get', 'view', 'read', 'check', 'is', 'has', 'can', 'balance',
            'totalSupply', 'name', 'symbol', 'decimals', 'owner', 'admin',
            'paused', 'pausedAt', 'paused_at', 'timelock', 'delay'
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
        """Track function definitions and analyze for time-lock requirements."""
        if not self.current_contract:
            return
            
        if ctx.identifier():
            self.current_function = ctx.identifier().getText()
        else:
            self.current_function = "unknown"
    
    def exitFunctionDefinition(self, ctx):
        """Analyze function for time-lock requirements when exiting."""
        if not self.current_contract or not self.current_function:
            return
        
        # Check if this is a critical function that should have time locks
        if self._is_critical_function():
            # Check if the function has time-lock mechanisms
            if not self._has_timelock_mechanism():
                violation = {
                    'type': 'SCWE-020',
                    'contract': self.current_contract,
                    'function': self.current_function,
                    'line': ctx.start.line,
                    'message': f"Function '{self.current_function}' is critical but lacks time-lock mechanism"
                }
                self.violations.append(violation)
        
        self.current_function = None
    
    def enterExpressionStatement(self, ctx):
        """Check for time-lock patterns in function bodies."""
        if not self.current_function or not self.current_contract:
            return
            
        expr_text = ctx.getText()
        line_number = ctx.start.line
        
        # Skip if already processed this line
        if line_number in self.processed_lines:
            return
        
        # Check for time-lock patterns
        if any(pattern in expr_text for pattern in self.timelock_patterns):
            self.processed_lines.add(line_number)
    
    def enterVariableDeclarationStatement(self, ctx):
        """Check for time-lock variables in function bodies."""
        if not self.current_function or not self.current_contract:
            return
            
        var_text = ctx.getText()
        line_number = ctx.start.line
        
        # Skip if already processed this line
        if line_number in self.processed_lines:
            return
        
        # Check for time-lock variable declarations
        if any(pattern in var_text for pattern in self.timelock_patterns):
            self.processed_lines.add(line_number)
    
    def _is_critical_function(self):
        """Check if the current function is critical and should have time locks."""
        if not self.current_function:
            return False
        
        func_lower = self.current_function.lower()
        
        # Skip public getter functions
        if any(public_func in func_lower for public_func in self.public_functions):
            return False
        
        # Check for critical function patterns
        return any(pattern in func_lower for pattern in self.critical_functions)
    
    def _has_timelock_mechanism(self):
        """Check if the current function has time-lock mechanisms."""
        # This is a simplified check - in a real implementation, you would
        # need to analyze the function body more thoroughly
        return len(self.processed_lines) > 0
    
    def get_violations(self):
        """Return all detected violations."""
        return self.violations
