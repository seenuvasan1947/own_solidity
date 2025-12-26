# S-CODE-019: Contract Name Reused
# Detects when multiple contracts have the same name in the codebase
# Can cause compilation artifacts to be overwritten and contracts to be unanalyzable

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re
from collections import defaultdict

class NameReusedDetector(SolidityParserListener):
    
    def __init__(self):
        self.violations = []
        self.contract_names = defaultdict(list)  # {name: [(file, line)]}
        self.current_file = "unknown"

    def set_current_file(self, filename):
        """Set the current file being analyzed"""
        self.current_file = filename

    def enterContractDefinition(self, ctx):
        contract_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        line = ctx.start.line
        
        # Track contract name and location
        self.contract_names[contract_name].append((self.current_file, line))

    def check_duplicates(self):
        """Check for duplicate contract names after parsing all files"""
        for contract_name, locations in self.contract_names.items():
            if len(locations) > 1:
                locations_str = '\n\t'.join([f"- {file} at line {line}" for file, line in locations])
                self.violations.append(
                    f"❌ [S-CODE-019] HIGH: Contract name reused: '{contract_name}' is defined in multiple locations:\n\t{locations_str}\n"
                    f"When compiling (especially with Truffle), only one contract will generate artifacts. "
                    f"This can lead to the wrong contract being deployed or analyzed. "
                    f"Rename one of the contracts to avoid conflicts."
                )

    def get_violations(self):
        """Return all detected violations"""
        self.check_duplicates()
        return self.violations
