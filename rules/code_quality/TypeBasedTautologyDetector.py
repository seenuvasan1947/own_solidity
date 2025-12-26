# S-CODE-030: Type-Based Tautology
# Detects comparisons that are always true or false based on type ranges
# Indicates logic errors or unnecessary checks

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class TypeBasedTautologyDetector(SolidityParserListener):
    
    # Type ranges for common Solidity types
    TYPE_RANGES = {
        'uint8': (0, 255),
        'uint16': (0, 65535),
        'uint32': (0, 4294967295),
        'uint64': (0, 18446744073709551615),
        'uint128': (0, 2**128 - 1),
        'uint256': (0, 2**256 - 1),
        'uint': (0, 2**256 - 1),
        'int8': (-128, 127),
        'int16': (-32768, 32767),
        'int32': (-2147483648, 2147483647),
        'int64': (-9223372036854775808, 9223372036854775807),
        'int128': (-(2**127), 2**127 - 1),
        'int256': (-(2**255), 2**255 - 1),
        'int': (-(2**255), 2**255 - 1),
    }
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None
        self.var_types = {}  # {var_name: type}

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"

    def exitContractDefinition(self, ctx):
        self.current_contract = None

    def enterFunctionDefinition(self, ctx):
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.var_types = {}
        
        # Extract parameter types
        func_text = ctx.getText()
        params = re.findall(r'(uint\d*|int\d*)\s+(\w+)', func_text)
        for type_name, var_name in params:
            self.var_types[var_name] = type_name

    def exitFunctionDefinition(self, ctx):
        self.in_function = False
        self.function_name = None

    def enterVariableDeclarationStatement(self, ctx):
        if self.in_function:
            var_text = ctx.getText()
            match = re.search(r'(uint\d*|int\d*)\s+(\w+)', var_text)
            if match:
                type_name, var_name = match.groups()
                self.var_types[var_name] = type_name

    def enterStatement(self, ctx):
        if not self.in_function:
            return
        
        stmt_text = ctx.getText()
        line = ctx.start.line
        
        # Check for tautologies/contradictions
        # Pattern: var >= constant, var <= constant, var > constant, var < constant
        for var_name, var_type in self.var_types.items():
            if var_type not in self.TYPE_RANGES:
                continue
            
            low, high = self.TYPE_RANGES[var_type]
            
            # Check >= 0 for unsigned types (always true)
            if re.search(rf'\b{var_name}\s*>=\s*0\b', stmt_text) and var_type.startswith('uint'):
                self.violations.append(
                    f"⚠️  [S-CODE-030] MEDIUM: Type-based tautology in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                    f"'{var_name} >= 0' is always true for {var_type}. Remove unnecessary check."
                )
            
            # Check < 0 for unsigned types (always false)
            if re.search(rf'\b{var_name}\s*<\s*0\b', stmt_text) and var_type.startswith('uint'):
                self.violations.append(
                    f"⚠️  [S-CODE-030] MEDIUM: Type-based contradiction in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                    f"'{var_name} < 0' is always false for {var_type}. Remove or fix condition."
                )
            
            # Check for comparisons beyond type range
            # Extract numeric constants
            numbers = re.findall(r'\b\d+\b', stmt_text)
            for num_str in numbers:
                try:
                    num = int(num_str)
                    # Check if comparison is always true/false
                    if re.search(rf'\b{var_name}\s*<\s*{num}\b', stmt_text) and num > high:
                        self.violations.append(
                            f"⚠️  [S-CODE-030] MEDIUM: Type-based tautology in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                            f"'{var_name} < {num}' is always true for {var_type} (max: {high})."
                        )
                except ValueError:
                    pass

    def get_violations(self):
        return self.violations
