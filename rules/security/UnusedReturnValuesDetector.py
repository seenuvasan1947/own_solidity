# S-SEC-021: Unused Return Values
# Detects external function calls where the return value is ignored
# Ignoring return values can lead to incorrect assumptions about call success

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class UnusedReturnValuesDetector(SolidityParserListener):
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None
        self.function_start_line = None
        self.return_value_vars = {}
        self.used_vars = set()

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"

    def exitContractDefinition(self, ctx):
        self.current_contract = None

    def enterFunctionDefinition(self, ctx):
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.function_start_line = ctx.start.line
        self.return_value_vars = {}
        self.used_vars = set()

    def exitFunctionDefinition(self, ctx):
        if self.in_function:
            for var_name, (line, call_expr) in self.return_value_vars.items():
                if var_name not in self.used_vars:
                    self.violations.append(
                        f"⚠️  [S-SEC-021] MEDIUM: Unused return value in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                        f"Return value '{var_name}' from external call is never used. "
                        f"Ensure the return value is used or the call is intentionally ignored."
                    )
        
        self.in_function = False
        self.function_name = None

    def enterStatement(self, ctx):
        if not self.in_function:
            return
        
        stmt_text = ctx.getText()
        line = ctx.start.line
        
        # Track variable assignments from external calls
        # Pattern: type varName = contract.function(...)
        call_match = re.search(r'(\w+)\s+(\w+)\s*=\s*\w+\.(\w+)\s*\(', stmt_text)
        if call_match and '.' in stmt_text:
            var_type = call_match.group(1)
            var_name = call_match.group(2)
            func_name = call_match.group(3)
            
            # Skip common patterns that are typically checked elsewhere
            skip_functions = ['transfer', 'transferFrom', 'send', 'call', 'delegatecall', 'staticcall']
            if func_name not in skip_functions:
                self.return_value_vars[var_name] = (line, func_name)
        
        # Track variable usage
        # Simple heuristic: if variable appears in the code after declaration, it's used
        for var_name in list(self.return_value_vars.keys()):
            if var_name in self.used_vars:
                continue
            
            # Check if variable is used in any meaningful way
            usage_patterns = [
                rf'\b{var_name}\s*[+\-*/]',  # Arithmetic
                rf'\b{var_name}\s*[<>=!]',   # Comparison
                rf'require\s*\([^)]*{var_name}',  # In require
                rf'if\s*\([^)]*{var_name}',       # In if
                rf'return\s+{var_name}',          # Returned
                rf'emit\s+\w+\([^)]*{var_name}',  # In event
                rf'{var_name}\s*\.',              # Member access
                rf'{var_name}\s*\[',              # Array access
            ]
            
            for pattern in usage_patterns:
                if re.search(pattern, stmt_text):
                    self.used_vars.add(var_name)
                    break

    def get_violations(self):
        return self.violations
