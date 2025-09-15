from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class UseOfTxOriginDetector(SolidityParserListener):
    """
    Detector for SCWE-018: Use of tx.origin for Authorization
    Rule Code: 018
    
    Detects usage of tx.origin for authorization instead of msg.sender.
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.current_function = None
        self.tx_origin_usage = []  # List of tx.origin usage locations
    
    def enterContractDefinition(self, ctx):
        """Track contract definitions."""
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "UnknownContract"
    
    def enterFunctionDefinition(self, ctx):
        """Track function definitions."""
        if not self.current_contract:
            return
            
        func_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.current_function = func_name
    
    def enterPrimaryExpression(self, ctx):
        """Check for tx.origin usage in expressions."""
        if not self.current_function or not self.current_contract:
            return
            
        expr_text = ctx.getText()
        
        # Check for tx.origin usage
        if 'tx.origin' in expr_text:
            # Check if it's used in authorization context
            if self._is_authorization_context(ctx):
                violation = {
                    'type': 'SCWE-018',
                    'contract': self.current_contract,
                    'function': self.current_function,
                    'line': ctx.start.line,
                    'message': f"Use of tx.origin for authorization in function '{self.current_function}' - should use msg.sender instead"
                }
                self.violations.append(violation)
    
    def enterExpressionStatement(self, ctx):
        """Check for tx.origin usage in expression statements."""
        if not self.current_function or not self.current_contract:
            return
            
        expr_text = ctx.getText()
        
        # Check for tx.origin usage in require statements
        if 'tx.origin' in expr_text and 'require(' in expr_text:
            violation = {
                'type': 'SCWE-018',
                'contract': self.current_contract,
                'function': self.current_function,
                'line': ctx.start.line,
                'message': f"Use of tx.origin in require statement in function '{self.current_function}' - should use msg.sender instead"
            }
            self.violations.append(violation)
    
    def enterIfStatement(self, ctx):
        """Check for tx.origin usage in if statements."""
        if not self.current_function or not self.current_contract:
            return
            
        expr_text = ctx.getText()
        
        # Check for tx.origin usage in if conditions
        if 'tx.origin' in expr_text:
            violation = {
                'type': 'SCWE-018',
                'contract': self.current_contract,
                'function': self.current_function,
                'line': ctx.start.line,
                'message': f"Use of tx.origin in if condition in function '{self.current_function}' - should use msg.sender instead"
            }
            self.violations.append(violation)
    
    def enterAssignment(self, ctx):
        """Check for tx.origin usage in assignments."""
        if not self.current_function or not self.current_contract:
            return
            
        # Get the right side of the assignment
        right_expr = ctx.expression(1) if len(ctx.expression()) > 1 else None
        if right_expr:
            expr_text = right_expr.getText()
            
            # Check for tx.origin usage in assignments
            if 'tx.origin' in expr_text:
                violation = {
                    'type': 'SCWE-018',
                    'contract': self.current_contract,
                    'function': self.current_function,
                    'line': ctx.start.line,
                    'message': f"Use of tx.origin in assignment in function '{self.current_function}' - should use msg.sender instead"
                }
                self.violations.append(violation)
    
    def _is_authorization_context(self, ctx):
        """Check if tx.origin is used in authorization context."""
        # Get the parent context to check for authorization patterns
        parent = ctx.parentCtx if hasattr(ctx, 'parentCtx') else None
        
        if parent:
            parent_text = parent.getText()
            
            # Check for common authorization patterns
            auth_patterns = [
                'require(', 'assert(', 'if (', '==', '!=', '&&', '||'
            ]
            
            return any(pattern in parent_text for pattern in auth_patterns)
        
        return False
    
    def get_violations(self):
        """Return list of detected violations."""
        return self.violations
