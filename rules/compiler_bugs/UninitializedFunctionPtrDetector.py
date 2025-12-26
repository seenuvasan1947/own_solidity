# S-BUG-008: Uninitialized Function Pointer in Constructor
# Detects calls to uninitialized function pointers in constructors (solc 0.4.5-0.5.8)
# Based on Slither's uninitialized_function_ptr_in_constructor detector
# Impact: LOW | Confidence: HIGH

from antlr4 import *
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class UninitializedFunctionPtrDetector(SolidityParserListener):
    """
    Detects uninitialized function pointer calls in constructors.
    
    Vulnerability: Solidity 0.4.5-0.5.8 has a bug where calling
    uninitialized function pointers in constructors leads to
    unexpected behavior.
    
    Example (Problematic):
        constructor() public {
            function(uint256) internal returns(uint256) a;
            a(10);  // BAD: 'a' is uninitialized
        }
    
    Recommendation: Initialize function pointers before calling,
    or avoid function pointers in constructors.
    """
    
    def __init__(self):
        self.violations = []
        self.in_constructor = False
        self.function_ptr_vars = set()
        self.solc_version = None
    
    def enterPragmaDirective(self, ctx):
        pragma_text = ctx.getText()
        version_match = re.search(r'(\d+)\.(\d+)\.(\d+)', pragma_text)
        if version_match:
            self.solc_version = (
                int(version_match.group(1)),
                int(version_match.group(2)),
                int(version_match.group(3))
            )
    
    def enterConstructorDefinition(self, ctx):
        self.in_constructor = True
        self.function_ptr_vars = set()
    
    def exitConstructorDefinition(self, ctx):
        self.in_constructor = False
    
    def enterVariableDeclarationStatement(self, ctx):
        if not self.in_constructor:
            return
        
        var_text = ctx.getText()
        line = ctx.start.line
        
        # Check for function pointer declarations
        if 'function(' in var_text and ('internal' in var_text or 'external' in var_text):
            # Extract variable name (simplified)
            if ctx.identifier():
                var_name = ctx.identifier().getText()
                self.function_ptr_vars.add(var_name)
    
    def enterExpressionStatement(self, ctx):
        if not self.in_constructor:
            return
        
        text = ctx.getText()
        line = ctx.start.line
        
        # Check for calls to function pointer variables
        for var_name in self.function_ptr_vars:
            if f"{var_name}(" in text:
                # Check if vulnerable version
                if self.solc_version:
                    major, minor, patch = self.solc_version
                    is_vulnerable = (
                        (major == 0 and minor == 4 and 5 <= patch <= 26) or
                        (major == 0 and minor == 5 and patch <= 8)
                    )
                    
                    if is_vulnerable:
                        self.violations.append(
                            f"❌ [S-BUG-008] Uninitialized function pointer call at line {line}: "
                            f"Calling function pointer '{var_name}' in constructor. "
                            f"Solidity 0.4.5-0.5.8 has a bug with uninitialized function pointers. "
                            f"Initialize before calling or upgrade to >= 0.5.9."
                        )
    
    def get_violations(self):
        return self.violations
