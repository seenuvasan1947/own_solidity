# S-SEC-019: Unchecked Send Return Value
# Detects send() calls where the return value is not checked
# Unchecked send can lead to silent failures and loss of funds

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class UncheckedSendDetector(SolidityParserListener):
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None
        self.function_start_line = None
        self.send_return_vars = {}
        self.checked_vars = set()

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"

    def exitContractDefinition(self, ctx):
        self.current_contract = None

    def enterFunctionDefinition(self, ctx):
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.function_start_line = ctx.start.line
        self.send_return_vars = {}
        self.checked_vars = set()

    def exitFunctionDefinition(self, ctx):
        if self.in_function:
            for var_name, line in self.send_return_vars.items():
                if var_name not in self.checked_vars:
                    self.violations.append(
                        f"❌ [S-SEC-019] MEDIUM: Unchecked send() return value in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                        f"Return value '{var_name}' from send() is not checked. "
                        f"Add validation: require({var_name}, \"Send failed\"); or use transfer() instead."
                    )
        
        self.in_function = False
        self.function_name = None

    def enterStatement(self, ctx):
        if not self.in_function:
            return
        
        stmt_text = ctx.getText()
        line = ctx.start.line
        
        # Check for send with return value assignment
        send_match = re.search(r'bool\s+(\w+)\s*=.*\.send\s*\(', stmt_text)
        if send_match:
            var_name = send_match.group(1)
            self.send_return_vars[var_name] = line
        elif '.send(' in stmt_text and not re.search(r'require\s*\(.*\.send', stmt_text):
            # Direct send without capturing return value
            self.violations.append(
                f"❌ [S-SEC-019] MEDIUM: Unchecked send() in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                f"send() return value is not captured or checked. Use transfer() or check the return value."
            )
        
        # Check for return value usage
        for var_name in list(self.send_return_vars.keys()):
            if var_name in self.checked_vars:
                continue
            
            check_patterns = [
                rf'require\s*\(\s*{var_name}',
                rf'assert\s*\(\s*{var_name}',
                rf'if\s*\(\s*!?\s*{var_name}',
            ]
            
            for pattern in check_patterns:
                if re.search(pattern, stmt_text):
                    self.checked_vars.add(var_name)
                    break

    def get_violations(self):
        return self.violations
