# S-OPT-005: Could Be Constant
# Detects state variables that could be declared constant
# Saves gas by storing in bytecode instead of storage

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class CouldBeConstantDetector(SolidityParserListener):
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.state_vars = {}  # {var_name: (line, initial_value)}
        self.modified_vars = set()

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.state_vars = {}
        self.modified_vars = set()

    def exitContractDefinition(self, ctx):
        # Check which state variables could be constant
        for var_name, (line, initial_value) in self.state_vars.items():
            if var_name not in self.modified_vars and initial_value:
                # Check if it's already constant or immutable
                if 'constant' not in initial_value and 'immutable' not in initial_value:
                    self.violations.append(
                        f"⚡ [S-OPT-005] OPTIMIZATION: State variable '{var_name}' in contract '{self.current_contract}' at line {line} could be constant: "
                        f"Variable is never modified after initialization. "
                        f"Declare as 'constant' to save gas."
                    )
        
        self.current_contract = None

    def enterStateVariableDeclaration(self, ctx):
        var_text = ctx.getText()
        line = ctx.start.line
        
        # Extract variable name and check if it has initial value
        match = re.search(r'(uint|uint256|int|address|bool|string|bytes\d*)\s+(?:public\s+|private\s+|internal\s+)?(constant\s+|immutable\s+)?(\w+)\s*=\s*(.+?);', var_text)
        if match:
            var_type, modifier, var_name, initial_value = match.groups()
            if not modifier:  # Not already constant or immutable
                self.state_vars[var_name] = (line, initial_value)

    def enterFunctionDefinition(self, ctx):
        func_text = ctx.getText()
        
        # Track state variable modifications
        for var_name in list(self.state_vars.keys()):
            # Check if variable is modified (assigned to)
            if re.search(rf'\b{var_name}\s*=', func_text):
                self.modified_vars.add(var_name)

    def get_violations(self):
        return self.violations
