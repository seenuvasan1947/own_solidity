# S-SEC-013: ABI encodePacked Collision
# Detects potential hash collisions from using multiple dynamic types in abi.encodePacked
# Can lead to signature/hash collisions and security vulnerabilities

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class EncodePackedCollisionDetector(SolidityParserListener):
    """
    Detects potential hash collisions from abi.encodePacked with multiple dynamic types.
    
    This detector identifies:
    1. abi.encodePacked() with multiple dynamic types (string, bytes, arrays)
    2. Potential collision scenarios in hash/signature generation
    3. Unsafe encoding patterns
    
    False Positive Mitigation:
    - Only flags when multiple dynamic types are present
    - Excludes single dynamic type usage (safe)
    - Excludes abi.encode() (safe alternative)
    - Checks for actual dynamic types (string, bytes, dynamic arrays)
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None
        self.function_start_line = None
        
        # Dynamic types that can cause collisions
        self.dynamic_types = ['string', 'bytes', 'bytes[]', 'string[]']

    def enterContractDefinition(self, ctx):
        """Track current contract"""
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"

    def exitContractDefinition(self, ctx):
        """Reset contract context"""
        self.current_contract = None

    def enterFunctionDefinition(self, ctx):
        """Track current function"""
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.function_start_line = ctx.start.line

    def exitFunctionDefinition(self, ctx):
        """Reset function context"""
        self.in_function = False
        self.function_name = None

    def enterStatement(self, ctx):
        """Check statements for abi.encodePacked usage"""
        if not self.in_function:
            return
        
        line = ctx.start.line
        text = ctx.getText()
        
        self._check_encode_packed(text, line)

    def enterExpressionStatement(self, ctx):
        """Check expression statements for abi.encodePacked"""
        if not self.in_function:
            return
        
        line = ctx.start.line
        text = ctx.getText()
        
        self._check_encode_packed(text, line)

    def _check_encode_packed(self, text, line):
        """Check for abi.encodePacked with multiple dynamic types"""
        text_lower = text.lower()
        
        # Check if abi.encodePacked is used
        if 'abi.encodepacked' not in text_lower:
            return
        
        # Extract arguments from abi.encodePacked(...)
        args = self._extract_encode_packed_args(text)
        
        if not args:
            return
        
        # Count dynamic type arguments
        dynamic_count = self._count_dynamic_args(args, text)
        
        # Report if multiple dynamic types
        if dynamic_count > 1:
            self.violations.append(
                f"❌ [S-SEC-013] CRITICAL: Hash collision risk in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                f"abi.encodePacked() called with {dynamic_count} dynamic type arguments. This can lead to hash collisions. "
                f"Use abi.encode() instead, or ensure only one dynamic type is used."
            )

    def _extract_encode_packed_args(self, text):
        """Extract arguments from abi.encodePacked call"""
        # Find abi.encodePacked(...)
        match = re.search(r'abi\.encodePacked\s*\((.*?)\)', text, re.IGNORECASE)
        if match:
            args_str = match.group(1)
            # Split by comma (simplified - doesn't handle nested calls perfectly)
            args = [arg.strip() for arg in args_str.split(',')]
            return args
        return []

    def _count_dynamic_args(self, args, full_text):
        """Count how many arguments are likely dynamic types"""
        dynamic_count = 0
        
        for arg in args:
            # Check if argument is a dynamic type
            if self._is_dynamic_type_arg(arg, full_text):
                dynamic_count += 1
        
        return dynamic_count

    def _is_dynamic_type_arg(self, arg, full_text):
        """Check if an argument is likely a dynamic type"""
        arg_lower = arg.lower()
        
        # Direct type indicators
        if any(dtype in arg_lower for dtype in ['string', 'bytes']):
            # Exclude fixed-size bytes (bytes1, bytes2, ..., bytes32)
            if not re.search(r'bytes\d+', arg_lower):
                return True
        
        # Check if it's an array access (likely dynamic array)
        if '[' in arg and ']' in arg:
            return True
        
        # Try to infer from variable name (heuristic)
        # Common patterns for dynamic types
        dynamic_patterns = ['name', 'message', 'data', 'text', 'content', 'doc', 'str']
        if any(pattern in arg_lower for pattern in dynamic_patterns):
            # Additional check: look for type declaration in function
            # This is a simplified heuristic
            return True
        
        return False

    def get_violations(self):
        """Return all detected violations"""
        return self.violations
