# S-ATR-004: Incorrect Solc Version
# Detects use of outdated or buggy Solidity compiler versions
# Based on Slither's incorrect_solc detector
# Impact: INFORMATIONAL | Confidence: HIGH

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class IncorrectSolcDetector(SolidityParserListener):
    """
    Detects use of outdated or problematic Solidity versions.
    
    Issues:
    - Old versions lack security features
    - Some versions have known bugs
    - Complex pragma statements are error-prone
    
    Example (Problematic):
        pragma solidity ^0.4.0;  // Too old
        pragma solidity <0.8.0;  // Uses less-than (discouraged)
    
    Recommendation: Use Solidity 0.8.0 or later with simple pragma.
    Example: pragma solidity ^0.8.0;
    """
    
    def __init__(self):
        self.violations = []
        self.pragma_checked = False
    
    def enterPragmaDirective(self, ctx):
        if self.pragma_checked:
            return
        
        pragma_text = ctx.getText()
        line = ctx.start.line
        
        if "solidity" not in pragma_text.lower():
            return
        
        self.pragma_checked = True
        
        # Extract version
        version_match = re.search(r'(\^|>|>=|<|<=)?\s*(\d+)\.(\d+)\.(\d+)', pragma_text)
        
        if not version_match:
            return
        
        operator = version_match.group(1) or ""
        major = int(version_match.group(2))
        minor = int(version_match.group(3))
        patch = int(version_match.group(4))
        
        # Check for old versions (< 0.8.0)
        if major == 0 and minor < 8:
            self.violations.append(
                f"⚠️ [S-ATR-004] Outdated Solidity version at line {line}: "
                f"{pragma_text}. Use Solidity 0.8.0 or later for better security features."
            )
        
        # Check for less-than operator (discouraged)
        if operator in ["<", "<="]:
            self.violations.append(
                f"⚠️ [S-ATR-004] Pragma uses less-than operator at line {line}: "
                f"{pragma_text}. This is discouraged. Use ^, >, or >= instead."
            )
        
        # Warn about very old versions
        if major == 0 and minor < 5:
            self.violations.append(
                f"❌ [S-ATR-004] Very outdated Solidity version at line {line}: "
                f"{pragma_text}. This version has known security issues. "
                f"Upgrade to 0.8.0 or later immediately."
            )
    
    def get_violations(self):
        return self.violations
