# S-BUG-007: ABIEncoderV2 Array
# Detects ABIEncoderV2 array encoding bug (solc 0.4.7-0.5.9)
# Based on Slither's storage_ABIEncoderV2_array detector
# Impact: HIGH | Confidence: HIGH

from antlr4 import *
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class ABIEncoderV2ArrayDetector(SolidityParserListener):
    """
    Detects ABIEncoderV2 storage array encoding bug.
    
    Vulnerability: Solidity 0.4.7-0.5.9 with ABIEncoderV2 incorrectly
    encodes storage arrays of arrays/structs when passed to abi.encode(),
    events, or external calls.
    
    Example (Problematic):
        pragma experimental ABIEncoderV2;
        
        uint[2][3] bad_arr = [[1, 2], [3, 4], [5, 6]];
        
        function bad() public {
            bytes memory b = abi.encode(bad_arr);  // Incorrect encoding!
        }
    
    Recommendation: Use Solidity >= 0.5.10.
    """
    
    def __init__(self):
        self.violations = []
        self.has_abiencoderv2 = False
        self.solc_version = None
        self.storage_arrays = set()  # Track storage array variables
        self.in_function = False
    
    def enterPragmaDirective(self, ctx):
        pragma_text = ctx.getText()
        
        # Check for ABIEncoderV2
        if 'experimental' in pragma_text and 'ABIEncoderV2' in pragma_text:
            self.has_abiencoderv2 = True
        
        # Check version
        version_match = re.search(r'(\d+)\.(\d+)\.(\d+)', pragma_text)
        if version_match:
            self.solc_version = (
                int(version_match.group(1)),
                int(version_match.group(2)),
                int(version_match.group(3))
            )
    
    def enterStateVariableDeclaration(self, ctx):
        var_text = ctx.getText()
        
        # Check for multi-dimensional arrays or arrays of structs
        if '[][]' in var_text or '][' in var_text:
            if ctx.identifier():
                var_name = ctx.identifier().getText()
                self.storage_arrays.add(var_name)
    
    def enterFunctionDefinition(self, ctx):
        self.in_function = True
    
    def exitFunctionDefinition(self, ctx):
        self.in_function = False
    
    def enterExpressionStatement(self, ctx):
        if not self.in_function or not self.has_abiencoderv2:
            return
        
        text = ctx.getText()
        line = ctx.start.line
        
        # Check for abi.encode with storage arrays
        if 'abi.encode(' in text:
            for arr_name in self.storage_arrays:
                if arr_name in text:
                    # Check if vulnerable version
                    if self.solc_version:
                        major, minor, patch = self.solc_version
                        is_vulnerable = (
                            (major == 0 and minor == 4 and patch >= 7) or
                            (major == 0 and minor == 5 and patch <= 9)
                        )
                        
                        if is_vulnerable:
                            self.violations.append(
                                f"❌ [S-BUG-007] ABIEncoderV2 array bug at line {line}: "
                                f"Encoding storage array '{arr_name}' with abi.encode(). "
                                f"Solidity 0.4.7-0.5.9 with ABIEncoderV2 incorrectly encodes "
                                f"storage arrays of arrays/structs. Upgrade to >= 0.5.10."
                            )
    
    def get_violations(self):
        return self.violations
