# S-BUG-002: Enum Conversion
# Detects dangerous enum conversions (solc < 0.4.5 issue)
# Based on Slither's enum_conversion detector
# Impact: MEDIUM | Confidence: HIGH

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class EnumConversionDetector(SolidityParserListener):
    """
    Detects dangerous enum conversions.
    
    Vulnerability: In Solidity < 0.4.5, converting out-of-range values to enums
    doesn't revert, leading to unexpected behavior.
    
    Example (Problematic):
        enum E { a, b, c }  // Valid values: 0, 1, 2
        
        function bug(uint x) public returns(E) {
            return E(x);  // BAD: x=3 doesn't revert in old versions
        }
    
    Recommendation: Use Solidity >= 0.4.5, or add manual range checks.
    """
    
    def __init__(self):
        self.violations = []
        self.enums = {}  # enum_name -> max_value
        self.in_function = False
        self.function_name = None
        self.solc_version = None
    
    def enterPragmaDirective(self, ctx):
        # Extract Solidity version
        pragma_text = ctx.getText()
        version_match = re.search(r'(\d+)\.(\d+)\.(\d+)', pragma_text)
        if version_match:
            major = int(version_match.group(1))
            minor = int(version_match.group(2))
            self.solc_version = (major, minor)
    
    def enterEnumDefinition(self, ctx):
        enum_name = ctx.identifier(0).getText() if ctx.identifier(0) else "unknown"
        # Count enum values
        enum_count = 0
        i = 1
        while True:
            if ctx.identifier(i):
                enum_count += 1
                i += 1
            else:
                break
        self.enums[enum_name] = enum_count - 1  # Max valid value
    
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
        
        # Check for enum conversions: EnumName(value)
        for enum_name in self.enums.keys():
            pattern = rf'{enum_name}\s*\('
            if re.search(pattern, text):
                # Only warn if using old Solidity version
                if self.solc_version and self.solc_version < (0, 4):
                    self.violations.append(
                        f"❌ [S-BUG-002] Dangerous enum conversion at line {line}: "
                        f"Converting to enum '{enum_name}' without range check. "
                        f"In Solidity < 0.4.5, out-of-range values don't revert. "
                        f"Upgrade to Solidity >= 0.4.5 or add manual range checks."
                    )
                elif not self.solc_version or self.solc_version < (0, 5):
                    self.violations.append(
                        f"⚠️ [S-BUG-002] Enum conversion at line {line}: "
                        f"Converting to enum '{enum_name}'. Ensure input is validated "
                        f"to be within valid range (0-{self.enums[enum_name]})."
                    )
    
    def get_violations(self):
        return self.violations
