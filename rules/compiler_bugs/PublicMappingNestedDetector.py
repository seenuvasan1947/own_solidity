# S-BUG-005: Public Mapping Nested
# Detects public mappings with nested structures (returns incorrect values in Solidity < 0.5)
# Based on Slither's public_mapping_nested detector  
# Impact: HIGH | Confidence: HIGH

from antlr4 import *
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class PublicMappingNestedDetector(SolidityParserListener):
    """
    Detects public mappings with nested structures.
    
    Vulnerability: Prior to Solidity 0.5, public mappings with nested
    structures returned incorrect values.
    
    Example (Problematic):
        struct Inner { uint x; }
        struct Outer { Inner inner; }
        mapping(address => Outer) public data;  // BAD in Solidity < 0.5
    
    Recommendation: Avoid public mappings with nested structures,
    or upgrade to Solidity >= 0.5.
    """
    
    def __init__(self):
        self.violations = []
        self.structs = {}  # struct_name -> has_nested_struct
        self.solc_version = None
    
    def enterPragmaDirective(self, ctx):
        pragma_text = ctx.getText()
        version_match = re.search(r'(\d+)\.(\d+)', pragma_text)
        if version_match:
            self.solc_version = (int(version_match.group(1)), int(version_match.group(2)))
    
    def enterStructDefinition(self, ctx):
        struct_name = ctx.identifier(0).getText() if ctx.identifier(0) else "unknown"
        # Check if struct has nested struct members (simplified detection)
        struct_text = ctx.getText()
        # Look for other struct types in members
        has_nested = any(s in struct_text for s in self.structs.keys())
        self.structs[struct_name] = has_nested
    
    def enterStateVariableDeclaration(self, ctx):
        var_text = ctx.getText()
        line = ctx.start.line
        
        # Check for public mapping
        if 'public' in var_text and 'mapping' in var_text:
            # Check if mapping value type is a struct
            for struct_name, has_nested in self.structs.items():
                if struct_name in var_text and has_nested:
                    if self.solc_version and self.solc_version < (0, 5):
                        self.violations.append(
                            f"❌ [S-BUG-005] Public mapping with nested structure at line {line}: "
                            f"Mapping uses struct '{struct_name}' which has nested structures. "
                            f"In Solidity < 0.5, this returns incorrect values. Upgrade to >= 0.5 "
                            f"or avoid public mappings with nested structures."
                        )
    
    def get_violations(self):
        return self.violations
