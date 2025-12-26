# S-SEC-023: Array Length Assignment
# Detects direct assignment to array.length with user-controlled values
# Can allow attackers to control all storage slots

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class ArrayLengthAssignmentDetector(SolidityParserListener):
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None
        self.function_params = set()

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"

    def exitContractDefinition(self, ctx):
        self.current_contract = None

    def enterFunctionDefinition(self, ctx):
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.function_params = set()
        
        # Extract function parameters
        func_text = ctx.getText()
        params = re.findall(r'\w+\s+(\w+)(?:\s*,|\s*\))', func_text)
        self.function_params = set(params)

    def exitFunctionDefinition(self, ctx):
        self.in_function = False
        self.function_name = None

    def enterStatement(self, ctx):
        if not self.in_function:
            return
        
        stmt_text = ctx.getText()
        line = ctx.start.line
        
        # Detect array.length = ...
        if re.search(r'\.length\s*=', stmt_text):
            # Check if right side uses function parameters or msg.sender
            is_user_controlled = any(param in stmt_text for param in self.function_params)
            is_user_controlled = is_user_controlled or 'msg.sender' in stmt_text or 'msg.value' in stmt_text
            
            if is_user_controlled:
                self.violations.append(
                    f"❌ [S-SEC-023] HIGH: Array length assignment with user-controlled value in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                    f"Direct assignment to array.length with user-controlled value detected. "
                    f"An attacker can set length to 2^256-1 to control all storage slots. "
                    f"Use push() to add elements instead of setting length directly."
                )

    def get_violations(self):
        return self.violations
