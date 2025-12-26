# S-SEC-020: Unchecked ERC20 Transfer
# Detects transfer/transferFrom calls where the return value is not checked
# Some tokens return false instead of reverting, leading to silent failures

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class UncheckedTransferDetector(SolidityParserListener):
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None
        self.function_start_line = None
        self.transfer_return_vars = {}
        self.checked_vars = set()
        self.uses_safe_erc20 = False

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.uses_safe_erc20 = False

    def exitContractDefinition(self, ctx):
        self.current_contract = None

    def enterImportDirective(self, ctx):
        import_text = ctx.getText()
        if 'SafeERC20' in import_text:
            self.uses_safe_erc20 = True

    def enterFunctionDefinition(self, ctx):
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.function_start_line = ctx.start.line
        self.transfer_return_vars = {}
        self.checked_vars = set()

    def exitFunctionDefinition(self, ctx):
        if self.in_function:
            for var_name, (line, call_type) in self.transfer_return_vars.items():
                if var_name not in self.checked_vars:
                    self.violations.append(
                        f"❌ [S-SEC-020] HIGH: Unchecked {call_type}() return value in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                        f"Return value from {call_type}() is not checked. Some tokens return false instead of reverting. "
                        f"Use SafeERC20 library or check the return value: require(token.{call_type}(...), \"Transfer failed\");"
                    )
        
        self.in_function = False
        self.function_name = None

    def enterStatement(self, ctx):
        if not self.in_function:
            return
        
        stmt_text = ctx.getText()
        line = ctx.start.line
        
        # Skip if using SafeERC20
        if 'safeTransfer' in stmt_text or 'safeTransferFrom' in stmt_text:
            return
        
        # Check for transfer with return value
        transfer_match = re.search(r'bool\s+(\w+)\s*=.*\.transfer\s*\(', stmt_text)
        if transfer_match:
            var_name = transfer_match.group(1)
            self.transfer_return_vars[var_name] = (line, 'transfer')
        elif re.search(r'\.transfer\s*\([^)]*\)\s*;', stmt_text) and not re.search(r'require\s*\(.*\.transfer', stmt_text):
            # Direct transfer without capturing return value (external call, not address.transfer)
            if not re.search(r'payable\s*\(', stmt_text):  # Exclude ETH transfers
                self.violations.append(
                    f"❌ [S-SEC-020] HIGH: Unchecked transfer() in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                    f"transfer() return value is not captured or checked. Use SafeERC20 or check the return value."
                )
        
        # Check for transferFrom with return value
        transferFrom_match = re.search(r'bool\s+(\w+)\s*=.*\.transferFrom\s*\(', stmt_text)
        if transferFrom_match:
            var_name = transferFrom_match.group(1)
            self.transfer_return_vars[var_name] = (line, 'transferFrom')
        elif re.search(r'\.transferFrom\s*\([^)]*\)\s*;', stmt_text) and not re.search(r'require\s*\(.*\.transferFrom', stmt_text):
            # Direct transferFrom without capturing return value
            self.violations.append(
                f"❌ [S-SEC-020] HIGH: Unchecked transferFrom() in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                f"transferFrom() return value is not captured or checked. Use SafeERC20 or check the return value."
            )
        
        # Check for return value usage
        for var_name in list(self.transfer_return_vars.keys()):
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
