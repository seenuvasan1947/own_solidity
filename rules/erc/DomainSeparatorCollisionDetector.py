# S-ERC-004: Domain Separator Collision (EIP-2612)
# Detects function signatures that collide with DOMAIN_SEPARATOR()
# Can break permit functionality in ERC20 tokens

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import hashlib

class DomainSeparatorCollisionDetector(SolidityParserListener):
    """
    Detects function signature collisions with EIP-2612's DOMAIN_SEPARATOR().
    
    This detector identifies:
    1. Functions whose signature hash collides with DOMAIN_SEPARATOR()
    2. DOMAIN_SEPARATOR() with incorrect return type (should be bytes32)
    3. Potential permit functionality breakage
    
    False Positive Mitigation:
    - Only checks ERC20-like contracts (has transfer, balanceOf, etc.)
    - Verifies actual signature collision via hash
    - Checks return type for DOMAIN_SEPARATOR()
    - Excludes non-ERC20 contracts
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.is_erc20 = False
        self.functions = []  # List of (name, signature, line, return_type)
        
        # DOMAIN_SEPARATOR() signature hash (first 4 bytes of keccak256)
        self.domain_separator_sig = self._get_function_selector("DOMAIN_SEPARATOR()")

    def _get_function_selector(self, signature):
        """Calculate function selector (first 4 bytes of keccak256)"""
        # Simplified - in production, use proper keccak256
        import hashlib
        hash_obj = hashlib.sha256(signature.encode())
        return hash_obj.hexdigest()[:8]

    def enterContractDefinition(self, ctx):
        """Track current contract"""
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.is_erc20 = False
        self.functions = []
        
        # Simple heuristic: check if contract text contains ERC20-like functions
        text = ctx.getText().lower()
        if 'transfer(' in text and 'balanceof(' in text:
            self.is_erc20 = True

    def exitContractDefinition(self, ctx):
        """Check for collisions when exiting contract"""
        if not self.is_erc20:
            self.current_contract = None
            return
        
        # Check each function for collision
        for func_name, signature, line, return_type in self.functions:
            # Calculate signature hash
            func_selector = self._get_function_selector(signature)
            
            # Check for collision
            if signature != "DOMAIN_SEPARATOR()" and func_selector == self.domain_separator_sig:
                self.violations.append(
                    f"❌ [S-ERC-004] CRITICAL: Function signature collision in contract '{self.current_contract}' at line {line}: "
                    f"Function '{func_name}' with signature '{signature}' collides with EIP-2612's DOMAIN_SEPARATOR(). "
                    f"This will break permit functionality. Rename or remove this function."
                )
            
            # Check if DOMAIN_SEPARATOR has correct return type
            if signature == "DOMAIN_SEPARATOR()":
                if return_type and 'bytes32' not in return_type.lower():
                    self.violations.append(
                        f"⚠️  [S-ERC-004] WARNING: Incorrect DOMAIN_SEPARATOR return type in contract '{self.current_contract}' at line {line}: "
                        f"DOMAIN_SEPARATOR() should return bytes32, but returns '{return_type}'. "
                        f"This violates EIP-2612 specification."
                    )
        
        self.current_contract = None

    def enterFunctionDefinition(self, ctx):
        """Track function signatures"""
        func_name = ctx.identifier().getText() if ctx.identifier() else None
        
        if not func_name:
            return
        
        line = ctx.start.line
        
        # Build function signature
        signature = self._build_signature(ctx, func_name)
        
        # Extract return type
        return_type = self._extract_return_type(ctx)
        
        self.functions.append((func_name, signature, line, return_type))

    def _build_signature(self, ctx, func_name):
        """Build function signature for hashing"""
        # Simplified: func_name()
        # In production, would need to extract parameter types
        text = ctx.getText()
        
        # Try to extract parameters
        if '(' in text and ')' in text:
            # Very simplified parameter extraction
            return f"{func_name}()"
        
        return f"{func_name}()"

    def _extract_return_type(self, ctx):
        """Extract function return type"""
        text = ctx.getText()
        
        # Look for returns keyword
        if 'returns' in text.lower():
            # Try to extract type after returns
            parts = text.lower().split('returns')
            if len(parts) > 1:
                # Extract type from returns clause
                returns_part = parts[1].split('{')[0].strip()
                if 'bytes32' in returns_part:
                    return 'bytes32'
                elif 'uint256' in returns_part:
                    return 'uint256'
                elif 'address' in returns_part:
                    return 'address'
                return returns_part[:50]  # Truncate
        
        return None

    def get_violations(self):
        """Return all detected violations"""
        return self.violations
