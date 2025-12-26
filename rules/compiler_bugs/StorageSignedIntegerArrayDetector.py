# S-BUG-003: Storage Signed Integer Array
# Detects storage signed integer array assignments (solc 0.4.7-0.5.9 bug)
# Based on Slither's storage_signed_integer_array detector
# Impact: HIGH | Confidence: MEDIUM

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class StorageSignedIntegerArrayDetector(SolidityParserListener):
    """
    Detects storage signed integer array assignments.
    
    Vulnerability: Solidity versions 0.4.7-0.5.9 have a compiler bug where
    assigning values to storage-allocated signed integer arrays can produce
    incorrect values.
    
    Example (Problematic):
        int[3] ether_balances;  // storage signed integer array
        
        function bad() private {
            ether_balances = [-1, -1, -1];  // BUG: May store wrong values
        }
    
    Recommendation: Use Solidity >= 0.5.10, or use unsigned integers/mappings.
    """
    
    def __init__(self):
        self.violations = []
        self.state_signed_int_arrays = set()  # Track state variables
        self.in_function = False
        self.function_name = None
        self.solc_version = None
        self.current_contract = None
    
    def enterPragmaDirective(self, ctx):
        # Extract Solidity version
        pragma_text = ctx.getText()
        version_match = re.search(r'(\d+)\.(\d+)\.(\d+)', pragma_text)
        if version_match:
            major = int(version_match.group(1))
            minor = int(version_match.group(2))
            patch = int(version_match.group(3))
            self.solc_version = (major, minor, patch)
    
    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.state_signed_int_arrays = set()
    
    def enterStateVariableDeclaration(self, ctx):
        # Check for signed integer arrays
        var_text = ctx.getText()
        
        # Look for signed integer array types: int[], int[N], int8[], etc.
        signed_int_array_pattern = r'int(\d+)?\s*\['
        if re.search(signed_int_array_pattern, var_text):
            # Extract variable name
            if ctx.identifier():
                var_name = ctx.identifier().getText()
                self.state_signed_int_arrays.add(var_name)
    
    def enterFunctionDefinition(self, ctx):
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
    
    def exitFunctionDefinition(self, ctx):
        self.in_function = False
    
    def enterExpressionStatement(self, ctx):
        if not self.in_function:
            return
        
        text = ctx.getText()
        line = ctx.start.line
        
        # Check if assigning to a signed integer array
        for var_name in self.state_signed_int_arrays:
            if f"{var_name}=" in text or f"{var_name}[" in text:
                # Check if vulnerable version
                if self.solc_version:
                    major, minor, patch = self.solc_version
                    is_vulnerable = (
                        (major == 0 and minor == 4 and patch >= 7) or
                        (major == 0 and minor == 5 and patch <= 9)
                    )
                    
                    if is_vulnerable:
                        self.violations.append(
                            f"❌ [S-BUG-003] Storage signed integer array assignment at line {line}: "
                            f"Variable '{var_name}' is a storage signed integer array. "
                            f"Solidity versions 0.4.7-0.5.9 have a compiler bug that can cause "
                            f"incorrect values. Upgrade to Solidity >= 0.5.10."
                        )
                    elif major == 0 and minor < 6:
                        self.violations.append(
                            f"⚠️ [S-BUG-003] Storage signed integer array assignment at line {line}: "
                            f"Variable '{var_name}' is a storage signed integer array. "
                            f"Consider upgrading to Solidity >= 0.5.10 to avoid potential compiler bugs."
                        )
    
    def get_violations(self):
        return self.violations
