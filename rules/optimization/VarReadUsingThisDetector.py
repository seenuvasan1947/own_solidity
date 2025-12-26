# S-OPT-007: Variable Read Using This
# Detects reading own public variables using this.varName()
# Adds unnecessary STATICCALL overhead

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class VarReadUsingThisDetector(SolidityParserListener):
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None
        self.public_vars = set()

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.public_vars = set()

    def exitContractDefinition(self, ctx):
        self.current_contract = None

    def enterStateVariableDeclaration(self, ctx):
        var_text = ctx.getText()
        
        # Extract public variable names
        if 'public' in var_text:
            match = re.search(r'public\s+(\w+)', var_text)
            if match:
                var_name = match.group(1)
                self.public_vars.add(var_name)

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
        
        # Detect this.varName() pattern
        for var_name in self.public_vars:
            if re.search(rf'this\.{var_name}\s*\(', stmt_text):
                self.violations.append(
                    f"⚡ [S-OPT-007] OPTIMIZATION: Reading variable using 'this' in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                    f"Reading 'this.{var_name}()' adds unnecessary STATICCALL overhead. "
                    f"Read '{var_name}' directly from storage."
                )

    def get_violations(self):
        return self.violations
