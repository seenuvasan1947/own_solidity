from antlr4 import *
from SolidityParserListener import SolidityParserListener

class InsecureOracleDataUpdatesDetector(SolidityParserListener):
    """
    Detector for SCWE-030: Insecure Oracle Data Updates
    Rule Code: 030
    
    Detects insecure oracle data updates including:
    - Unrestricted oracle update functions
    - Missing access control for oracle updates
    - Absence of validation for oracle data
    - Lack of timelock mechanisms for oracle updates
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.current_function = None
        self.processed_lines = set()
        self.function_has_secure_updates = {}
        
        # Oracle update patterns
        self.update_patterns = [
            'updatePrice', 'updateData', 'updateValue', 'setPrice', 'setData',
            'setValue', 'changePrice', 'changeData', 'modifyPrice', 'modifyData',
            'oracle', 'price', 'data', 'value', 'feed'
        ]
        
        # Access control patterns
        self.access_control_patterns = [
            'onlyOwner', 'onlyAdmin', 'onlyGovernance', 'onlyRole',
            'require(msg.sender ==', 'require(owner ==', 'require(admin ==',
            'require(hasRole', 'require(isOwner', 'require(isAdmin',
            'modifier', 'Modifier'
        ]
        
        # Validation patterns
        self.validation_patterns = [
            'require(', 'assert(', 'if (', 'validation', 'validate',
            'check', 'verify', 'confirm', 'approve'
        ]
        
        # Timelock patterns
        self.timelock_patterns = [
            'timelock', 'timeLock', 'delay', 'wait', 'cooldown',
            'block.timestamp', 'block.number', 'now', 'time'
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
        
        # Initialize secure update tracking for this function
        if self.current_function:
            self.function_has_secure_updates[self.current_function] = False
    
    def exitFunctionDefinition(self, ctx):
        """Analyze function for secure oracle updates when exiting."""
        if not self.current_contract or not self.current_function:
            return
        
        # Check if this function updates oracle data and needs security
        if self._is_oracle_update_function():
            # Check if the function has secure update mechanisms
            if not self.function_has_secure_updates.get(self.current_function, False):
                violation = {
                    'type': 'SCWE-030',
                    'contract': self.current_contract,
                    'function': self.current_function,
                    'line': ctx.start.line,
                    'message': f"Function '{self.current_function}' updates oracle data without proper security"
                }
                self.violations.append(violation)
        
        self.current_function = None
    
    def enterExpressionStatement(self, ctx):
        """Check for secure update patterns in function bodies."""
        if not self.current_function or not self.current_contract:
            return
            
        expr_text = ctx.getText()
        
        # Check for access control, validation, or timelock patterns
        if (any(pattern in expr_text for pattern in self.access_control_patterns) or
            any(pattern in expr_text for pattern in self.validation_patterns) or
            any(pattern in expr_text for pattern in self.timelock_patterns)):
            self.function_has_secure_updates[self.current_function] = True
    
    def enterVariableDeclarationStatement(self, ctx):
        """Check for secure update variables in function bodies."""
        if not self.current_function or not self.current_contract:
            return
            
        var_text = ctx.getText()
        
        # Check for timelock variable declarations
        if any(pattern in var_text for pattern in self.timelock_patterns):
            self.function_has_secure_updates[self.current_function] = True
    
    def _is_oracle_update_function(self):
        """Check if the current function is likely to update oracle data."""
        if not self.current_function:
            return False
        
        func_lower = self.current_function.lower()
        return any(pattern.lower() in func_lower for pattern in self.update_patterns)
    
    def get_violations(self):
        """Return all detected violations."""
        return self.violations
