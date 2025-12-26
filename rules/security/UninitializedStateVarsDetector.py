# S-SEC-033: Uninitialized State Variables
# Detects state variables that are never initialized
# Can lead to unexpected zero values

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class UninitializedStateVarsDetector(SolidityParserListener):
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.state_vars = {}  # {var_name: line}
        self.initialized_vars = set()

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.state_vars = {}
        self.initialized_vars = set()

    def exitContractDefinition(self, ctx):
        # Check which state variables are never initialized
        for var_name, line in self.state_vars.items():
            if var_name not in self.initialized_vars:
                self.violations.append(
                    f"❌ [S-SEC-033] HIGH: Uninitialized state variable in contract '{self.current_contract}' at line {line}: "
                    f"Variable '{var_name}' is never initialized. "
                    f"Initialize in declaration or constructor."
                )
        
        self.current_contract = None

    def enterStateVariableDeclaration(self, ctx):
        var_text = ctx.getText()
        line = ctx.start.line
        
        # Extract variable name
        match = re.search(r'(uint|uint256|int|address|bool|string|bytes\d*)\s+(?:public\s+|private\s+|internal\s+)?(\w+)', var_text)
        if match:
            var_type, var_name = match.groups()
            self.state_vars[var_name] = line
            
            # Check if initialized in declaration
            if '=' in var_text:
                self.initialized_vars.add(var_name)

    def enterFunctionDefinition(self, ctx):
        func_text = ctx.getText()
        
        # Track state variable assignments in functions
        for var_name in list(self.state_vars.keys()):
            if re.search(rf'\b{var_name}\s*=', func_text):
                self.initialized_vars.add(var_name)

    def get_violations(self):
        return self.violations
