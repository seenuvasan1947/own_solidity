from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class DeprecatedUsageDetector(SolidityParserListener):
    """
    Rule Code: 009
    Detects SCWE-009: Deprecated Variable and Function Usage vulnerabilities
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.current_function = None
        
        # Define deprecated functions and their alternatives
        self.deprecated_functions = {
            'transfer': {
                'alternative': 'Use payable(recipient).transfer(amount) or call{value: amount}("")',
                'description': 'Direct transfer on address is deprecated'
            },
            'send': {
                'alternative': 'Use call{value: amount}("") with proper error handling',
                'description': 'send() function is deprecated due to gas limit issues'
            },
            'callcode': {
                'alternative': 'Use delegatecall or call instead',
                'description': 'callcode is deprecated in favor of delegatecall'
            },
            'suicide': {
                'alternative': 'Use selfdestruct instead',
                'description': 'suicide is deprecated in favor of selfdestruct'
            },
            'throw': {
                'alternative': 'Use require(), assert(), or revert() instead',
                'description': 'throw is deprecated in favor of require/assert/revert'
            }
        }
        
        # Define deprecated global variables
        self.deprecated_globals = {
            'now': {
                'alternative': 'Use block.timestamp instead',
                'description': 'now is deprecated in favor of block.timestamp'
            },
            'msg': {
                'alternative': 'Use msg.sender, msg.value, msg.data separately',
                'description': 'Direct msg usage is deprecated'
            }
        }
        
    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"
        
    def exitContractDefinition(self, ctx):
        self.current_contract = None
        
    def enterFunctionDefinition(self, ctx):
        self.current_function = ctx.identifier().getText() if ctx.identifier() else "unknown"
        
    def exitFunctionDefinition(self, ctx):
        self.current_function = None
        
    def enterMemberAccess(self, ctx):
        """Detect deprecated member access patterns"""
        if not ctx.identifier():
            return
            
        member_name = ctx.identifier().getText()
        line = ctx.start.line
        
        # Get the full expression to check context
        full_expr = ctx.getText()
        
        # Check for deprecated function calls, but avoid false positives
        if member_name in self.deprecated_functions:
            # Skip if it's payable(recipient).transfer() which is the modern approach
            if member_name == 'transfer' and 'payable(' in full_expr:
                return
            # Skip if it's using call{value: amount}("") which is modern
            if member_name == 'send' and 'call{' in full_expr:
                return
                
            deprecation_info = self.deprecated_functions[member_name]
            self.violations.append(
                f"SCWE-009: Deprecated function usage '{member_name}' in contract '{self.current_contract}' "
                f"at line {line}: {deprecation_info['description']}. "
                f"Alternative: {deprecation_info['alternative']}"
            )
            
    def enterFunctionCall(self, ctx):
        """Detect deprecated function calls"""
        # Get the function name from the expression
        expr = ctx.expression()
        if expr:
            func_name = self._get_function_name_from_expression(expr)
            if func_name and func_name in self.deprecated_functions:
                line = ctx.start.line
                full_expr = ctx.getText()
                
                # Skip if it's payable(recipient).transfer() which is the modern approach
                if func_name == 'transfer' and 'payable(' in full_expr:
                    return
                # Skip if it's using call{value: amount}("") which is modern
                if func_name == 'send' and 'call{' in full_expr:
                    return
                    
                deprecation_info = self.deprecated_functions[func_name]
                self.violations.append(
                    f"SCWE-009: Deprecated function call '{func_name}' in contract '{self.current_contract}' "
                    f"at line {line}: {deprecation_info['description']}. "
                    f"Alternative: {deprecation_info['alternative']}"
                )
                
    def enterPrimaryExpression(self, ctx):
        """Detect deprecated global variables"""
        if not hasattr(ctx, 'getText'):
            return
            
        expr_text = ctx.getText()
        line = ctx.start.line
        
        # Check for deprecated global variables
        for deprecated_var, info in self.deprecated_globals.items():
            if expr_text == deprecated_var:
                self.violations.append(
                    f"SCWE-009: Deprecated global variable '{deprecated_var}' in contract '{self.current_contract}' "
                    f"at line {line}: {info['description']}. "
                    f"Alternative: {info['alternative']}"
                )
                
    def enterIdentifier(self, ctx):
        """Detect deprecated identifiers"""
        identifier_text = ctx.getText()
        line = ctx.start.line
        
        # Check for deprecated global variables
        if identifier_text in self.deprecated_globals:
            deprecation_info = self.deprecated_globals[identifier_text]
            self.violations.append(
                f"SCWE-009: Deprecated identifier '{identifier_text}' in contract '{self.current_contract}' "
                f"at line {line}: {deprecation_info['description']}. "
                f"Alternative: {deprecation_info['alternative']}"
            )
            
    def _get_function_name_from_expression(self, expr_ctx):
        """Extract function name from expression context"""
        try:
            # Handle member access (e.g., recipient.transfer)
            if hasattr(expr_ctx, 'identifier') and expr_ctx.identifier():
                return expr_ctx.identifier().getText()
            # Handle direct function calls
            elif hasattr(expr_ctx, 'getText'):
                return expr_ctx.getText()
        except Exception:
            pass
        return None

    def get_violations(self):
        return self.violations
