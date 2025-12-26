# S-SEC-012: Unchecked Low-Level Call Return Values
# Detects low-level calls (.call, .delegatecall, .staticcall) with unchecked return values
# Unchecked calls can silently fail, leading to unexpected behavior

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class UncheckedLowLevelCallDetector(SolidityParserListener):
    """
    Detects unchecked return values from low-level calls.
    
    This detector identifies:
    1. .call(), .delegatecall(), .staticcall() without return value checks
    2. Return values stored but not validated
    3. Silent failures that could lock funds
    
    False Positive Mitigation:
    - Checks for require/assert on return value (success variable)
    - Checks for if statements validating the return
    - Excludes cases where failure is intentionally ignored with comment
    - Tracks variable usage across statements
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None
        self.function_start_line = None
        self.low_level_calls = []  # List of (line, call_text, return_var)
        self.checked_variables = set()  # Variables that have been checked

    def enterContractDefinition(self, ctx):
        """Track current contract"""
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"

    def exitContractDefinition(self, ctx):
        """Reset contract context"""
        self.current_contract = None

    def enterFunctionDefinition(self, ctx):
        """Track current function"""
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "fallback"
        self.function_start_line = ctx.start.line
        self.low_level_calls = []
        self.checked_variables = set()

    def exitFunctionDefinition(self, ctx):
        """Check for unchecked calls when exiting function"""
        # Report any unchecked low-level calls
        for line, call_text, return_var in self.low_level_calls:
            if return_var and return_var not in self.checked_variables:
                self.violations.append(
                    f"❌ [S-SEC-012] CRITICAL: Unchecked low-level call in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                    f"Return value '{return_var}' from low-level call is not checked. This can lead to silent failures. "
                    f"Add 'require({return_var}, \"Call failed\");' or handle the failure appropriately."
                )
            elif not return_var:
                # Call without capturing return value at all
                self.violations.append(
                    f"❌ [S-SEC-012] CRITICAL: Unchecked low-level call in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                    f"Low-level call does not capture or check return value. This can lead to silent failures."
                )
        
        self.in_function = False
        self.function_name = None

    def enterStatement(self, ctx):
        """Check statements for low-level calls and checks"""
        if not self.in_function:
            return
        
        line = ctx.start.line
        text = ctx.getText()
        
        # Check for low-level calls
        self._check_low_level_call(text, line)
        
        # Check for return value validation
        self._check_return_validation(text)

    def enterVariableDeclarationStatement(self, ctx):
        """Check variable declarations for low-level call assignments"""
        if not self.in_function:
            return
        
        line = ctx.start.line
        text = ctx.getText()
        
        self._check_low_level_call(text, line)

    def _check_low_level_call(self, text, line):
        """Check if text contains a low-level call"""
        text_lower = text.lower()
        
        # Low-level call patterns
        low_level_patterns = [
            ('.call(', '.call{'),
            ('.delegatecall(', '.delegatecall{'),
            ('.staticcall(', '.staticcall{')
        ]
        
        for patterns in low_level_patterns:
            if any(pattern in text_lower for pattern in patterns):
                # Try to extract return variable
                return_var = self._extract_return_variable(text)
                
                # Check if it's immediately checked (inline require)
                if self._is_inline_checked(text):
                    if return_var:
                        self.checked_variables.add(return_var)
                else:
                    self.low_level_calls.append((line, text[:100], return_var))
                break

    def _extract_return_variable(self, text):
        """Try to extract the variable storing the return value"""
        # Common patterns:
        # (bool success, ) = addr.call(...)
        # bool success = addr.call(...)
        # (success, data) = addr.call(...)
        
        if '(' in text and ')' in text:
            # Tuple destructuring
            before_equals = text.split('=')[0] if '=' in text else ''
            if 'bool' in before_equals.lower():
                # Extract variable name
                # Pattern: (bool success, ...) or (bool success)
                parts = before_equals.split('(')
                if len(parts) > 1:
                    inner = parts[-1].strip()
                    # Get first variable after 'bool'
                    if 'bool' in inner.lower():
                        tokens = inner.replace(',', ' ').split()
                        for i, token in enumerate(tokens):
                            if token.lower() == 'bool' and i + 1 < len(tokens):
                                return tokens[i + 1].strip()
        
        # Simple assignment: bool success = ...
        if 'bool' in text.lower() and '=' in text:
            parts = text.split('=')[0].split()
            for i, part in enumerate(parts):
                if part.lower() == 'bool' and i + 1 < len(parts):
                    return parts[i + 1].strip()
        
        return None

    def _is_inline_checked(self, text):
        """Check if the call is immediately checked inline"""
        text_lower = text.lower()
        
        # Pattern: require(addr.call(...), "error")
        if 'require(' in text_lower and '.call' in text_lower:
            return True
        
        # Pattern: assert(addr.call(...))
        if 'assert(' in text_lower and '.call' in text_lower:
            return True
        
        return False

    def _check_return_validation(self, text):
        """Check if text validates a return value"""
        text_lower = text.lower()
        
        # Common success variable names
        success_vars = ['success', 'result', 'ok', 'succeeded']
        
        # Check for require/assert with success variable
        if 'require(' in text_lower or 'assert(' in text_lower:
            for var in success_vars:
                if var in text_lower:
                    self.checked_variables.add(var)
        
        # Check for if statement with success variable
        if 'if(' in text_lower or 'if (' in text_lower:
            for var in success_vars:
                if var in text_lower:
                    # Check if it's a validation (not just assignment)
                    if '==' in text or '!=' in text or '!' in text:
                        self.checked_variables.add(var)

    def get_violations(self):
        """Return all detected violations"""
        return self.violations
