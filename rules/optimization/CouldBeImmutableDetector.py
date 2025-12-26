# S-OPT-006: Could Be Immutable
# Detects state variables that could be declared immutable
# Saves gas by storing in bytecode instead of storage

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class CouldBeImmutableDetector(SolidityParserListener):
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.state_vars = {}  # {var_name: line}
        self.constructor_assigned = set()
        self.modified_after_constructor = set()
        self.in_constructor = False

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.state_vars = {}
        self.constructor_assigned = set()
        self.modified_after_constructor = set()

    def exitContractDefinition(self, ctx):
        # Check which state variables could be immutable
        for var_name, line in self.state_vars.items():
            if var_name in self.constructor_assigned and var_name not in self.modified_after_constructor:
                self.violations.append(
                    f"⚡ [S-OPT-006] OPTIMIZATION: State variable '{var_name}' in contract '{self.current_contract}' at line {line} could be immutable: "
                    f"Variable is only set in constructor. "
                    f"Declare as 'immutable' to save gas."
                )
        
        self.current_contract = None

    def enterStateVariableDeclaration(self, ctx):
        var_text = ctx.getText()
        line = ctx.start.line
        
        # Extract variable name
        match = re.search(r'(uint|uint256|int|address|bool|string|bytes\d*)\s+(?:public\s+|private\s+|internal\s+)?(constant\s+|immutable\s+)?(\w+)', var_text)
        if match:
            var_type, modifier, var_name = match.groups()
            if not modifier:  # Not already constant or immutable
                self.state_vars[var_name] = line

    def enterConstructorDefinition(self, ctx):
        self.in_constructor = True

    def exitConstructorDefinition(self, ctx):
        self.in_constructor = False

    def enterFunctionDefinition(self, ctx):
        if ctx.getText().startswith('constructor'):
            self.in_constructor = True
        else:
            self.in_constructor = False

    def exitFunctionDefinition(self, ctx):
        self.in_constructor = False

    def enterStatement(self, ctx):
        stmt_text = ctx.getText()
        
        # Track state variable assignments
        for var_name in list(self.state_vars.keys()):
            if re.search(rf'\b{var_name}\s*=', stmt_text):
                if self.in_constructor:
                    self.constructor_assigned.add(var_name)
                else:
                    self.modified_after_constructor.add(var_name)

    def get_violations(self):
        return self.violations
