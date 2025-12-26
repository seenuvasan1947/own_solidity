# S-SEC-018: Unchecked Low-Level Call Return Values
# Detects low-level calls where the return value is not checked
# Unchecked calls can lead to silent failures and loss of funds

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class UncheckedLowLevelReturnValuesDetector(SolidityParserListener):
    """
    Detects unchecked return values from low-level calls.
    
    This detector identifies:
    1. .call() without checking return value
    2. .delegatecall() without checking return value
    3. .staticcall() without checking return value
    4. Return values stored but never used
    
    False Positive Mitigation:
    - Checks if return value is assigned and used
    - Checks for require/assert on return value
    - Checks for if statements checking success
    - Excludes try-catch wrapped calls
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None
        self.function_start_line = None
        self.in_try_catch = False
        self.low_level_call_vars = {}  # {var_name: line}
        self.checked_vars = set()

    def enterContractDefinition(self, ctx):
        """Track current contract"""
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"

    def exitContractDefinition(self, ctx):
        """Reset contract context"""
        self.current_contract = None

    def enterFunctionDefinition(self, ctx):
        """Track current function"""
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.function_start_line = ctx.start.line
        self.low_level_call_vars = {}
        self.checked_vars = set()

    def exitFunctionDefinition(self, ctx):
        """Check for unchecked return values"""
        if self.in_function:
            # Report unchecked variables
            for var_name, line in self.low_level_call_vars.items():
                if var_name not in self.checked_vars:
                    self.violations.append(
                        f"❌ [S-SEC-018] MEDIUM: Unchecked low-level call return value in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                        f"Return value '{var_name}' from low-level call is not checked. "
                        f"Add validation: require({var_name}, \"Call failed\");"
                    )
        
        self.in_function = False
        self.function_name = None

    def enterTryStatement(self, ctx):
        """Track try-catch blocks"""
        self.in_try_catch = True

    def exitTryStatement(self, ctx):
        """Exit try-catch block"""
        self.in_try_catch = False

    def enterStatement(self, ctx):
        """Check statements for low-level calls and their usage"""
        if not self.in_function:
            return
        
        stmt_text = ctx.getText()
        line = ctx.start.line
        
        # Skip if in try-catch (already handled)
        if self.in_try_catch:
            return
        
        # Check for low-level calls with return value assignment
        self._check_low_level_call_assignment(stmt_text, line)
        
        # Check for return value usage in require/assert/if
        self._check_return_value_usage(stmt_text)

    def _check_low_level_call_assignment(self, text, line):
        """Check for low-level call return value assignments"""
        # Pattern: (bool success, ) = addr.call(...)
        # Pattern: bool success = addr.call(...)
        
        low_level_patterns = [
            (r'\(bool\s+(\w+)\s*,', r'\.call'),           # (bool success, bytes memory data) = addr.call(...)
            (r'bool\s+(\w+)\s*=.*\.call', r'\.call'),     # bool success = addr.call(...)
            (r'\(bool\s+(\w+)\s*,', r'\.delegatecall'),   # delegatecall
            (r'bool\s+(\w+)\s*=.*\.delegatecall', r'\.delegatecall'),
            (r'\(bool\s+(\w+)\s*,', r'\.staticcall'),     # staticcall
            (r'bool\s+(\w+)\s*=.*\.staticcall', r'\.staticcall'),
        ]
        
        for var_pattern, call_pattern in low_level_patterns:
            if re.search(call_pattern, text):
                var_match = re.search(var_pattern, text)
                if var_match:
                    var_name = var_match.group(1)
                    self.low_level_call_vars[var_name] = line
                else:
                    # Call without capturing return value - immediate violation
                    if not re.search(r'require\s*\(.*\.call', text) and not re.search(r'assert\s*\(.*\.call', text):
                        self.violations.append(
                            f"❌ [S-SEC-018] MEDIUM: Unchecked low-level call in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                            f"Low-level call return value is not captured or checked. "
                            f"Capture and check: (bool success, ) = addr.call(...); require(success, \"Call failed\");"
                        )

    def _check_return_value_usage(self, text):
        """Check if return values are used in validation"""
        # Check for require/assert/if with the return value variable
        for var_name in list(self.low_level_call_vars.keys()):
            if var_name in self.checked_vars:
                continue
            
            # Patterns for checking the return value
            check_patterns = [
                rf'require\s*\(\s*{var_name}',
                rf'assert\s*\(\s*{var_name}',
                rf'if\s*\(\s*!?\s*{var_name}',
                rf'if\s*\(\s*{var_name}\s*==\s*true',
                rf'if\s*\(\s*{var_name}\s*==\s*false',
            ]
            
            for pattern in check_patterns:
                if re.search(pattern, text):
                    self.checked_vars.add(var_name)
                    break

    def get_violations(self):
        """Return all detected violations"""
        return self.violations
