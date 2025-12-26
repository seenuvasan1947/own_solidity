# S-CODE-036: Unused State Variables
# Detects state variables that are never used
# Wastes storage and gas

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class UnusedStateVarsDetector(SolidityParserListener):
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.state_vars = {}  # {var_name: (line, visibility)}
        self.used_vars = set()

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.state_vars = {}
        self.used_vars = set()

    def exitContractDefinition(self, ctx):
        # Check which state variables are unused
        for var_name, (line, visibility) in self.state_vars.items():
            # Skip public variables (they have auto-generated getters)
            if visibility != 'public' and var_name not in self.used_vars:
                self.violations.append(
                    f"ℹ️  [S-CODE-036] INFO: Unused state variable in contract '{self.current_contract}' at line {line}: "
                    f"Variable '{var_name}' is never used. "
                    f"Remove unused variable to save gas."
                )
        
        self.current_contract = None

    def enterStateVariableDeclaration(self, ctx):
        var_text = ctx.getText()
        line = ctx.start.line
        
        # Extract variable name and visibility
        match = re.search(r'(uint|uint256|int|address|bool|string|bytes\d*|mapping)\s*(?:\([^)]*\))?\s+(public|private|internal)?\s*(\w+)', var_text)
        if match:
            var_type, visibility, var_name = match.groups()
            visibility = visibility or 'internal'  # Default visibility
            self.state_vars[var_name] = (line, visibility)

    def enterFunctionDefinition(self, ctx):
        func_text = ctx.getText()
        
        # Track state variable usage
        for var_name in list(self.state_vars.keys()):
            if re.search(rf'\b{var_name}\b', func_text):
                self.used_vars.add(var_name)

    def get_violations(self):
        return self.violations
