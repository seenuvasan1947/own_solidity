# S-ATR-003: Different Pragma Directives
# Detects use of different Solidity versions across files
# Based on Slither's constant_pragma detector
# Impact: INFORMATIONAL | Confidence: HIGH

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class DifferentPragmaDetector(SolidityParserListener):
    """
    Detects if different pragma directives are used.
    
    Issue: Using different Solidity versions can lead to inconsistencies.
    
    Example (Problematic):
        File1.sol: pragma solidity ^0.8.0;
        File2.sol: pragma solidity ^0.7.0;  // Different version
    
    Recommendation: Use one consistent Solidity version across all files.
    
    Note: This detector works per-file. For multi-file analysis, 
    violations should be aggregated at project level.
    """
    
    def __init__(self):
        self.violations = []
        self.pragma_versions = []
    
    def enterPragmaDirective(self, ctx):
        # Extract pragma version
        pragma_text = ctx.getText()
        if "solidity" in pragma_text.lower():
            # Extract version part
            version = pragma_text.replace("pragma", "").replace("solidity", "").replace(";", "").strip()
            if version and version not in self.pragma_versions:
                self.pragma_versions.append(version)
    
    def get_violations(self):
        # This detector is more useful for multi-file analysis
        # For now, we just track pragma versions
        # In a real implementation, this would compare across files
        if len(self.pragma_versions) > 1:
            versions_str = ", ".join(self.pragma_versions)
            self.violations.append(
                f"⚠️ [S-ATR-003] Multiple pragma versions found in file: {versions_str}. "
                f"Use a single consistent Solidity version."
            )
        return self.violations
