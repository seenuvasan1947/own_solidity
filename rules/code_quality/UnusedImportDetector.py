# S-CODE-032: Unused Import
# Detects import statements that are not used in the contract
# Clutters code and wastes gas during compilation

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class UnusedImportDetector(SolidityParserListener):
    
    def __init__(self):
        self.violations = []
        self.imports = []  # [(line, import_path, imported_items)]
        self.file_content = ""

    def set_source(self, source_code):
        """Set the source code for analysis"""
        self.file_content = source_code

    def enterImportDirective(self, ctx):
        import_text = ctx.getText()
        line = ctx.start.line
        
        # Extract import path and items
        # Pattern: import "path" or import {A, B} from "path" or import * as Name from "path"
        path_match = re.search(r'["\']([^"\']+)["\']', import_text)
        if path_match:
            import_path = path_match.group(1)
            
            # Extract imported items
            items_match = re.search(r'\{([^}]+)\}', import_text)
            if items_match:
                items = [item.strip() for item in items_match.group(1).split(',')]
            else:
                # import "path" or import * as Name
                alias_match = re.search(r'as\s+(\w+)', import_text)
                if alias_match:
                    items = [alias_match.group(1)]
                else:
                    # Simple import, extract filename
                    filename = import_path.split('/')[-1].replace('.sol', '')
                    items = [filename]
            
            self.imports.append((line, import_path, items))

    def check_unused_imports(self):
        """Check which imports are not used"""
        for line, path, items in self.imports:
            for item in items:
                # Check if item is used in the file
                # Simple heuristic: search for the identifier in the code
                if not re.search(rf'\b{re.escape(item)}\b', self.file_content):
                    self.violations.append(
                        f"ℹ️  [S-CODE-032] INFO: Unused import at line {line}: "
                        f"'{item}' from '{path}' is imported but not used. "
                        f"Remove unused import to clean up code."
                    )

    def get_violations(self):
        self.check_unused_imports()
        return self.violations
