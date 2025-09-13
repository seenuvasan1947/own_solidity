from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class HardcodedConstantsDetector(SolidityParserListener):
    """
    Rule Code: 008
    Detects SCWE-008: Hardcoded Constants vulnerabilities
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.current_function = None
        self.in_assignment = False
        self.assignment_target = None
        
    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"
        
    def exitContractDefinition(self, ctx):
        self.current_contract = None
        
    def enterFunctionDefinition(self, ctx):
        self.current_function = ctx.identifier().getText() if ctx.identifier() else "unknown"
        
    def exitFunctionDefinition(self, ctx):
        self.current_function = None
        
    def enterAssignment(self, ctx):
        """Detect assignment expressions that might contain hardcoded constants"""
        self.in_assignment = True
        
        # Get the target of the assignment
        left_expr = ctx.expression(0)
        if left_expr:
            self.assignment_target = self._get_identifier_from_expression(left_expr)
        
        # Check the right side for hardcoded constants
        right_expr = ctx.expression(1)
        if right_expr:
            self._check_expression_for_hardcoded_constants(right_expr, ctx.start.line)
            
    def exitAssignment(self, ctx):
        self.in_assignment = False
        self.assignment_target = None
        
    def enterStateVariableDeclaration(self, ctx):
        """Check state variable declarations for hardcoded initial values"""
        var_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        var_line = ctx.start.line
        
        # Check if there's an initial value assignment
        if ctx.initialValue:
            self._check_expression_for_hardcoded_constants(ctx.initialValue, var_line, var_name)
            
    def enterConstantVariableDeclaration(self, ctx):
        """Check constant variable declarations for hardcoded values"""
        var_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        var_line = ctx.start.line
        
        # Constants are always hardcoded by definition, but we should flag them
        if ctx.initialValue:
            self._check_expression_for_hardcoded_constants(ctx.initialValue, var_line, var_name, is_constant=True)
            
    def enterVariableDeclarationStatement(self, ctx):
        """Check local variable declarations for hardcoded initial values"""
        if not self.current_function:
            return
            
        # Handle single variable declaration
        if ctx.variableDeclaration():
            var_decl = ctx.variableDeclaration()
            var_name = var_decl.identifier().getText() if var_decl.identifier() else "unknown"
            var_line = ctx.start.line
            
            # Check if there's an initial value assignment
            if ctx.expression():
                self._check_expression_for_hardcoded_constants(ctx.expression(), var_line, var_name)
        
        # Handle tuple variable declaration
        elif ctx.variableDeclarationTuple():
            var_line = ctx.start.line
            if ctx.expression():
                self._check_expression_for_hardcoded_constants(ctx.expression(), var_line, "tuple variables")
                
    def _check_expression_for_hardcoded_constants(self, expr_ctx, line, var_name=None, is_constant=False):
        """Check if an expression contains hardcoded constants"""
        expr_text = expr_ctx.getText()
        
        # Check for hardcoded addresses (40 hex characters starting with 0x)
        if self._is_hardcoded_address(expr_text):
            context = f" in variable '{var_name}'" if var_name else ""
            const_type = "constant" if is_constant else "hardcoded"
            self.violations.append(
                f"SCWE-008: {const_type.capitalize()} address constant{context} at line {line}: "
                f"Address '{expr_text}' should be configurable rather than hardcoded."
            )
            
        # Check for hardcoded large numbers (potential magic numbers)
        elif self._is_hardcoded_large_number(expr_text):
            context = f" in variable '{var_name}'" if var_name else ""
            const_type = "constant" if is_constant else "hardcoded"
            self.violations.append(
                f"SCWE-008: {const_type.capitalize()} numeric constant{context} at line {line}: "
                f"Number '{expr_text}' should be configurable rather than hardcoded."
            )
            
        # Check for hardcoded strings (non-empty strings)
        elif self._is_hardcoded_string(expr_text):
            context = f" in variable '{var_name}'" if var_name else ""
            const_type = "constant" if is_constant else "hardcoded"
            self.violations.append(
                f"SCWE-008: {const_type.capitalize()} string constant{context} at line {line}: "
                f"String '{expr_text}' should be configurable rather than hardcoded."
            )
            
    def _is_hardcoded_address(self, text):
        """Check if text represents a hardcoded Ethereum address"""
        # Ethereum addresses are 40 hex characters starting with 0x
        import re
        return re.match(r'^0x[a-fA-F0-9]{40}$', text) is not None
        
    def _is_hardcoded_large_number(self, text):
        """Check if text represents a hardcoded large number"""
        try:
            # Remove any whitespace and check if it's a number
            clean_text = text.strip()
            
            # Check for decimal numbers
            if clean_text.isdigit():
                num = int(clean_text)
                # Flag numbers that are likely to be configuration values (not 0, 1, or small numbers)
                return num > 100 and num != 1000 and num != 10000  # Common but configurable values
                
            # Check for hex numbers
            if clean_text.startswith('0x'):
                hex_part = clean_text[2:]
                if all(c in '0123456789abcdefABCDEF' for c in hex_part):
                    num = int(hex_part, 16)
                    return num > 100
                    
        except (ValueError, AttributeError):
            pass
        return False
        
    def _is_hardcoded_string(self, text):
        """Check if text represents a hardcoded string"""
        # Check for quoted strings that are not empty and not just whitespace
        if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
            content = text[1:-1]  # Remove quotes
            # Flag non-empty strings that might be configuration values
            return len(content.strip()) > 0 and not content.strip() in ['', ' ', '\t', '\n']
        return False
        
    def _get_identifier_from_expression(self, expr_ctx):
        """Extract identifier from an expression context"""
        try:
            # Try to get identifier from member access
            if hasattr(expr_ctx, 'identifier') and expr_ctx.identifier():
                return expr_ctx.identifier().getText()
            # Try to get identifier from primary expression
            elif hasattr(expr_ctx, 'getText'):
                return expr_ctx.getText()
        except Exception:
            pass
        return None

    def get_violations(self):
        return self.violations
