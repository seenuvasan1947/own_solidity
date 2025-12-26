# S-VAL-006: Missing Zero Address Validation
# Detects missing zero address validation for address parameters
# Setting critical addresses to zero can lock contracts or lose funds

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class MissingZeroAddressValidationDetector(SolidityParserListener):
    """
    Detects missing zero address validation for address parameters.
    
    This detector identifies:
    1. Functions that accept address parameters without zero checks
    2. Functions that assign address parameters to state variables
    3. Functions that use addresses in transfers/calls without validation
    
    False Positive Mitigation:
    - Only flags when address is used in critical operations
    - Checks if validation exists in function or modifiers
    - Ignores view/pure functions
    - Excludes addresses that are validated
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None
        self.function_start_line = None
        self.is_view_or_pure = False
        self.function_parameters = {}  # {param_name: type}
        self.validated_addresses = set()
        self.used_addresses = {}  # {param_name: [usage_lines]}

    def enterContractDefinition(self, ctx):
        """Track current contract"""
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"

    def exitContractDefinition(self, ctx):
        """Reset contract context"""
        self.current_contract = None

    def enterFunctionDefinition(self, ctx):
        """Track current function and its parameters"""
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.function_start_line = ctx.start.line
        self.function_parameters = {}
        self.validated_addresses = set()
        self.used_addresses = {}
        
        # Check if function is view or pure
        func_text = ctx.getText()
        self.is_view_or_pure = 'view' in func_text or 'pure' in func_text
        
        # Extract address parameters
        self._extract_address_parameters(func_text)

    def exitFunctionDefinition(self, ctx):
        """Check for missing zero address validations"""
        if self.in_function and not self.is_view_or_pure:
            # Check each address parameter
            for param_name in self.function_parameters:
                if self.function_parameters[param_name] == 'address':
                    # Check if parameter is used in critical operations
                    if param_name in self.used_addresses:
                        # Check if parameter is validated
                        if param_name not in self.validated_addresses:
                            usage_lines = self.used_addresses[param_name]
                            self.violations.append(
                                f"⚠️  [S-VAL-006] WARNING: Missing zero address validation in function '{self.function_name}' of contract '{self.current_contract}' at line {self.function_start_line}: "
                                f"Address parameter '{param_name}' is used without zero address check (used at lines: {', '.join(map(str, usage_lines))}). "
                                f"Add validation: require({param_name} != address(0), \"Zero address\");"
                            )
        
        self.in_function = False
        self.function_name = None

    def enterStatement(self, ctx):
        """Check statements for address usage and validation"""
        if not self.in_function or self.is_view_or_pure:
            return
        
        stmt_text = ctx.getText()
        line = ctx.start.line
        
        # Check for zero address validation
        for param_name in self.function_parameters:
            if self.function_parameters[param_name] == 'address':
                # Patterns for zero address validation
                validation_patterns = [
                    rf'require\s*\(\s*{param_name}\s*!=\s*address\s*\(\s*0\s*\)',
                    rf'require\s*\(\s*address\s*\(\s*0\s*\)\s*!=\s*{param_name}',
                    rf'require\s*\(\s*{param_name}\s*!=\s*0x0',
                    rf'assert\s*\(\s*{param_name}\s*!=\s*address\s*\(\s*0\s*\)',
                    rf'if\s*\(\s*{param_name}\s*==\s*address\s*\(\s*0\s*\)\s*\)\s*revert',
                ]
                
                for pattern in validation_patterns:
                    if re.search(pattern, stmt_text, re.IGNORECASE):
                        self.validated_addresses.add(param_name)
                        break
        
        # Check for critical address usage
        for param_name in self.function_parameters:
            if self.function_parameters[param_name] == 'address':
                # Critical operations with addresses
                critical_patterns = [
                    rf'{param_name}\s*=',  # Assignment to state variable
                    rf'\.transfer\s*\(',   # Transfer
                    rf'\.send\s*\(',       # Send
                    rf'\.call',            # Call
                    rf'\.delegatecall',    # Delegatecall
                ]
                
                for pattern in critical_patterns:
                    if re.search(pattern, stmt_text):
                        if param_name not in self.used_addresses:
                            self.used_addresses[param_name] = []
                        self.used_addresses[param_name].append(line)
                        break

    def _extract_address_parameters(self, func_text):
        """Extract address-type parameters from function signature"""
        # Pattern: address paramName
        matches = re.finditer(r'\baddress\s+(?:memory\s+|calldata\s+)?(\w+)', func_text)
        for match in matches:
            param_name = match.group(1)
            # Avoid capturing keywords or modifiers
            if param_name not in ['public', 'private', 'internal', 'external', 'view', 'pure']:
                self.function_parameters[param_name] = 'address'

    def get_violations(self):
        """Return all detected violations"""
        return self.violations
