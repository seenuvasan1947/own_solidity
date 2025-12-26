# S-SEC-016: ABI EncodePacked Hash Collision Detection
# Detects dangerous usage of abi.encodePacked with multiple dynamic types
# This can lead to hash collisions and signature vulnerabilities

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class ABIEncodePackedCollisionDetector(SolidityParserListener):
    """
    Detects dangerous usage of abi.encodePacked with multiple dynamic types.
    
    This detector identifies:
    1. abi.encodePacked with multiple string arguments
    2. abi.encodePacked with multiple bytes arguments
    3. abi.encodePacked with multiple dynamic arrays
    4. Usage in keccak256 (signature generation)
    
    False Positive Mitigation:
    - Only flags when multiple dynamic types are present
    - Ignores single dynamic type usage
    - Ignores usage with only fixed-size types
    - Checks if used in security-critical contexts (keccak256, signatures)
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None
        self.function_start_line = None
        
        # Dynamic types that can cause collisions
        self.dynamic_types = ['string', 'bytes', 'uint[]', 'address[]', 'bytes32[]']

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

    def enterExpression(self, ctx):
        """Check expressions for abi.encodePacked usage"""
        if not self.in_function:
            return
        
        expr_text = ctx.getText()
        
        # Check for abi.encodePacked
        if 'abi.encodePacked' not in expr_text:
            return
        
        self._check_encode_packed_collision(expr_text, ctx.start.line)

    def enterFunctionCall(self, ctx):
        """Check function calls for abi.encodePacked"""
        if not self.in_function:
            return
        
        call_text = ctx.getText()
        
        # Check for abi.encodePacked
        if 'abi.encodePacked' not in call_text:
            return
        
        self._check_encode_packed_collision(call_text, ctx.start.line)

    def _check_encode_packed_collision(self, text, line):
        """Check if abi.encodePacked usage can lead to collision"""
        # Extract the arguments to abi.encodePacked
        # Pattern: abi.encodePacked(arg1, arg2, ...)
        match = re.search(r'abi\.encodePacked\s*\(([^)]+)\)', text)
        if not match:
            return
        
        args_text = match.group(1)
        
        # Count dynamic type indicators
        dynamic_count = 0
        found_dynamic_types = []
        
        # Check for string literals or variables
        if args_text.count('"') >= 4 or args_text.count("'") >= 4:
            # Multiple string literals
            dynamic_count += args_text.count('"') // 2 + args_text.count("'") // 2
            found_dynamic_types.append('string')
        
        # Check for common dynamic type patterns
        # Look for function parameters or variables that might be dynamic
        args_list = self._split_arguments(args_text)
        
        for arg in args_list:
            arg_lower = arg.strip().lower()
            
            # Skip empty or very short args
            if len(arg_lower) < 2:
                continue
            
            # Check if argument looks like a dynamic type
            # Heuristics: contains certain keywords or patterns
            if any(dtype in arg_lower for dtype in ['string', 'bytes', '[]']):
                dynamic_count += 1
                if 'string' in arg_lower:
                    found_dynamic_types.append('string')
                elif 'bytes' in arg_lower and 'bytes32' not in arg_lower:
                    found_dynamic_types.append('bytes')
                elif '[]' in arg_lower:
                    found_dynamic_types.append('array')
        
        # Also check the broader context for parameter types
        # This is a simplified check - in real implementation would need full type analysis
        
        # If we have multiple arguments and at least 2 look dynamic, flag it
        if len(args_list) >= 2 and dynamic_count >= 2:
            # Check if used in security-critical context
            is_in_keccak = 'keccak256' in text or 'sha256' in text
            is_in_signature = any(keyword in text.lower() for keyword in [
                'signature', 'hash', 'verify', 'recover', 'sign'
            ])
            
            severity = "CRITICAL" if (is_in_keccak or is_in_signature) else "HIGH"
            symbol = "❌" if severity == "CRITICAL" else "⚠️ "
            
            dynamic_types_str = ', '.join(set(found_dynamic_types)) if found_dynamic_types else 'dynamic types'
            
            self.violations.append(
                f"{symbol} [S-SEC-016] {severity}: Hash collision risk in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                f"Using abi.encodePacked with multiple dynamic arguments ({dynamic_types_str}). "
                f"This can lead to hash collisions. Use abi.encode() instead for security-critical operations."
            )

    def _split_arguments(self, args_text):
        """Split function arguments, respecting nested parentheses and commas"""
        args = []
        current_arg = ""
        paren_depth = 0
        
        for char in args_text:
            if char == '(':
                paren_depth += 1
                current_arg += char
            elif char == ')':
                paren_depth -= 1
                current_arg += char
            elif char == ',' and paren_depth == 0:
                args.append(current_arg.strip())
                current_arg = ""
            else:
                current_arg += char
        
        if current_arg.strip():
            args.append(current_arg.strip())
        
        return args

    def get_violations(self):
        """Return all detected violations"""
        return self.violations
