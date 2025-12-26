# S-CODE-017: Local Variable Shadowing
# Detects local variables that shadow state variables, functions, modifiers, or events
# Can cause confusion and bugs

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class LocalShadowingDetector(SolidityParserListener):
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.state_variables = set()
        self.functions = set()
        self.modifiers = set()
        self.events = set()
        self.in_function = False
        self.function_name = None

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.state_variables = set()
        self.functions = set()
        self.modifiers = set()
        self.events = set()

    def exitContractDefinition(self, ctx):
        self.current_contract = None

    def enterStateVariableDeclaration(self, ctx):
        var_text = ctx.getText()
        match = re.search(r'\b(\w+)\s*(?:=|;)', var_text)
        if match:
            var_name = match.group(1)
            if var_name not in ['uint', 'uint256', 'address', 'bool', 'string', 'bytes', 'mapping']:
                self.state_variables.add(var_name)

    def enterFunctionDefinition(self, ctx):
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.functions.add(self.function_name)

    def exitFunctionDefinition(self, ctx):
        self.in_function = False
        self.function_name = None

    def enterModifierDefinition(self, ctx):
        modifier_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.modifiers.add(modifier_name)

    def enterEventDefinition(self, ctx):
        event_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.events.add(event_name)

    def enterVariableDeclarationStatement(self, ctx):
        if not self.in_function:
            return
        
        var_text = ctx.getText()
        line = ctx.start.line
        
        # Extract local variable name
        match = re.search(r'\b(\w+)\s*(?:=|;)', var_text)
        if match:
            var_name = match.group(1)
            
            # Skip type names
            if var_name in ['uint', 'uint256', 'address', 'bool', 'string', 'bytes', 'memory', 'storage', 'calldata']:
                return
            
            shadowed_items = []
            
            # Check what it shadows
            if var_name in self.state_variables:
                shadowed_items.append(('state variable', var_name))
            if var_name in self.functions:
                shadowed_items.append(('function', var_name))
            if var_name in self.modifiers:
                shadowed_items.append(('modifier', var_name))
            if var_name in self.events:
                shadowed_items.append(('event', var_name))
            
            if shadowed_items:
                shadowed_desc = ', '.join([f"{item[0]} '{item[1]}'" for item in shadowed_items])
                self.violations.append(
                    f"⚠️  [S-CODE-017] LOW: Local variable shadowing in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                    f"Local variable '{var_name}' shadows {shadowed_desc}. "
                    f"Rename the local variable to avoid confusion."
                )

    def get_violations(self):
        return self.violations
