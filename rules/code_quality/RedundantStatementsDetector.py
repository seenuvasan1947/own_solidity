# S-CODE-027: Redundant Statements
# Detects statements that have no effect
# Wastes gas and clutters code

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class RedundantStatementsDetector(SolidityParserListener):
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"

    def exitContractDefinition(self, ctx):
        self.current_contract = None

    def enterFunctionDefinition(self, ctx):
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"

    def exitFunctionDefinition(self, ctx):
        self.in_function = False
        self.function_name = None

    def enterStatement(self, ctx):
        if not self.in_function:
            return
        
        stmt_text = ctx.getText()
        line = ctx.start.line
        
        # Detect redundant type names (e.g., "uint;", "bool;")
        type_patterns = [
            r'^\s*uint\s*;',
            r'^\s*uint256\s*;',
            r'^\s*int\s*;',
            r'^\s*bool\s*;',
            r'^\s*address\s*;',
            r'^\s*string\s*;',
            r'^\s*bytes\s*;',
        ]
        
        for pattern in type_patterns:
            if re.search(pattern, stmt_text):
                self.violations.append(
                    f"ℹ️  [S-CODE-027] INFO: Redundant statement in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                    f"Statement has no effect. Remove it."
                )
                return
        
        # Detect redundant identifiers (e.g., "assert;", "require;", function names)
        # Pattern: single identifier followed by semicolon
        if re.match(r'^\s*\w+\s*;$', stmt_text):
            # Skip if it's a function call (has parentheses before semicolon in full context)
            if '(' not in stmt_text:
                self.violations.append(
                    f"ℹ️  [S-CODE-027] INFO: Redundant statement in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                    f"Statement '{stmt_text.strip()}' has no effect. Remove it."
                )

    def get_violations(self):
        return self.violations
