from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class InsecureABIEncodingDetector(SolidityParserListener):
    """
    Rule Code: 011
    Detects SCWE-011: Insecure ABI Encoding and Decoding vulnerabilities
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.current_function = None
        self.processed_lines = set()  # Track processed lines to avoid duplicates
        
    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"
        
    def exitContractDefinition(self, ctx):
        self.current_contract = None
        
    def enterFunctionDefinition(self, ctx):
        self.current_function = ctx.identifier().getText() if ctx.identifier() else "unknown"
        
    def exitFunctionDefinition(self, ctx):
        self.current_function = None
        
    def enterFunctionCall(self, ctx):
        """Detect insecure ABI encoding/decoding function calls"""
        expr = ctx.expression()
        if not expr:
            return
            
        # Get the full function call text
        full_call = ctx.getText()
        line = ctx.start.line
        
        # Check for abi.encodePacked() usage (insecure for hashing)
        if 'abi.encodePacked(' in full_call and line not in self.processed_lines:
            self.processed_lines.add(line)
            # Check if it's used with keccak256 (collision risk)
            if self._is_used_with_keccak256(ctx):
                self.violations.append(
                    f"SCWE-011: Insecure ABI encoding detected in contract '{self.current_contract}' "
                    f"at line {line}: abi.encodePacked() used with keccak256() creates collision risk. "
                    f"Use abi.encode() instead for secure hashing."
                )
            else:
                # Only flag if it's not in a non-hashing context
                if not self._is_non_hashing_context(ctx):
                    self.violations.append(
                        f"SCWE-011: Potentially insecure ABI encoding detected in contract '{self.current_contract}' "
                        f"at line {line}: abi.encodePacked() can cause collision risks. "
                        f"Consider using abi.encode() for better security."
                    )
        
        # Check for abi.decode() usage (potential for type confusion)
        elif 'abi.decode(' in full_call and line not in self.processed_lines:
            self.processed_lines.add(line)
            # Only flag if there's no validation around it
            if not self._has_validation_around_decode(ctx):
                self.violations.append(
                    f"SCWE-011: ABI decoding detected in contract '{self.current_contract}' "
                    f"at line {line}: abi.decode() usage detected. "
                    f"Ensure proper validation and type matching to prevent memory corruption."
                )
            
    def enterMemberAccess(self, ctx):
        """Detect ABI function access patterns"""
        if not ctx.identifier():
            return
            
        member_name = ctx.identifier().getText()
        line = ctx.start.line
        
        # Check for direct abi.encodePacked access
        if member_name == 'encodePacked' and line not in self.processed_lines:
            # Get the full expression to check context
            full_expr = ctx.getText()
            if 'abi.' in full_expr:
                # Only flag if it's not in a non-hashing context
                if not self._is_non_hashing_context(ctx):
                    self.violations.append(
                        f"SCWE-011: Insecure ABI encoding access detected in contract '{self.current_contract}' "
                        f"at line {line}: abi.encodePacked access detected. "
                        f"Consider using abi.encode() for better security."
                    )
        
        # Check for direct abi.decode access
        elif member_name == 'decode' and line not in self.processed_lines:
            full_expr = ctx.getText()
            if 'abi.' in full_expr:
                # Only flag if there's no validation around it
                if not self._has_validation_around_decode(ctx):
                    self.violations.append(
                        f"SCWE-011: ABI decoding access detected in contract '{self.current_contract}' "
                        f"at line {line}: abi.decode access detected. "
                        f"Ensure proper validation and type matching."
                    )
                
    def _is_used_with_keccak256(self, ctx):
        """Check if the function call is used with keccak256"""
        # Get the parent context to check if this is inside a keccak256 call
        parent = ctx.parentCtx
        while parent:
            if hasattr(parent, 'getText'):
                parent_text = parent.getText()
                # Check if this specific abi.encodePacked call is inside a keccak256 call
                if 'keccak256(' in parent_text:
                    # Make sure the abi.encodePacked is actually inside the keccak256 call
                    # by checking if the current context is a direct child of the keccak256 call
                    if hasattr(parent, 'expression') and parent.expression() == ctx:
                        return True
            parent = parent.parentCtx
        return False
        
    def _is_non_hashing_context(self, ctx):
        """Check if abi.encodePacked is used in a non-hashing context (acceptable)"""
        # Get the parent context to check if this is NOT used with keccak256
        parent = ctx.parentCtx
        while parent:
            if hasattr(parent, 'getText'):
                parent_text = parent.getText()
                # If it's used with keccak256, it's a hashing context (insecure)
                if 'keccak256(' in parent_text:
                    return False
                # If it's just returned or assigned, it might be acceptable
                if 'return' in parent_text or '=' in parent_text:
                    return True
            parent = parent.parentCtx
        
        # If we can't find keccak256 in the context, it's likely non-hashing
        return True
        
    def _has_validation_around_decode(self, ctx):
        """Check if abi.decode is used with proper validation"""
        # Get the parent context to check for validation
        parent = ctx.parentCtx
        while parent:
            if hasattr(parent, 'getText'):
                parent_text = parent.getText()
                # Check for validation patterns
                if 'require(' in parent_text or 'assert(' in parent_text:
                    return True
                # Check if it's in a try-catch block
                if 'try' in parent_text or 'catch' in parent_text:
                    return True
            parent = parent.parentCtx
        return False

    def get_violations(self):
        return self.violations
