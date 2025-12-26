# S-OPT-002: Cache Array Length in Loops
# Detects for loops that repeatedly access array.length without caching it
# Caching array length can save significant gas in loops

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class CacheArrayLengthDetector(SolidityParserListener):
    """
    Detects for loops that use array.length in loop condition without caching.
    
    This detector identifies:
    1. For loops with array.length in condition
    2. Storage arrays (not memory arrays - less critical)
    3. Loops that don't modify the array length
    
    False Positive Mitigation:
    - Ignores memory arrays (lower gas impact)
    - Ignores loops that modify array (push/pop operations)
    - Ignores loops with external calls (array might change)
    - Only flags storage arrays
    - Checks if length is already cached before loop
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None
        self.function_start_line = None
        self.in_for_loop = False
        self.for_loop_depth = 0
        self.current_for_condition = None
        self.current_for_body = None
        self.current_for_line = None
        
        # Track variable declarations
        self.local_variables = {}  # {var_name: type}
        self.state_variables = {}  # {var_name: type}
        
        # Track cached lengths
        self.cached_lengths = set()  # Set of array names that have been cached

    def enterContractDefinition(self, ctx):
        """Track current contract"""
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.state_variables = {}

    def exitContractDefinition(self, ctx):
        """Reset contract context"""
        self.current_contract = None
        self.state_variables = {}

    def enterStateVariableDeclaration(self, ctx):
        """Track state variables to identify storage arrays"""
        var_text = ctx.getText()
        # Simple pattern to detect arrays
        if '[]' in var_text:
            # Extract variable name
            match = re.search(r'(\w+)\s*;', var_text)
            if match:
                var_name = match.group(1)
                self.state_variables[var_name] = 'array'

    def enterFunctionDefinition(self, ctx):
        """Track current function"""
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.function_start_line = ctx.start.line
        self.local_variables = {}
        self.cached_lengths = set()

    def exitFunctionDefinition(self, ctx):
        """Reset function context"""
        self.in_function = False
        self.function_name = None
        self.local_variables = {}
        self.cached_lengths = set()

    def enterVariableDeclarationStatement(self, ctx):
        """Track local variable declarations and check for cached lengths"""
        if not self.in_function:
            return
        
        var_text = ctx.getText()
        
        # Check if this is caching an array length
        # Pattern: uint len = array.length;
        length_cache_match = re.search(r'(\w+)\s*=\s*(\w+)\.length', var_text)
        if length_cache_match:
            array_name = length_cache_match.group(2)
            self.cached_lengths.add(array_name)
        
        # Track memory arrays
        if 'memory' in var_text and '[]' in var_text:
            match = re.search(r'(\w+)\s*;', var_text)
            if match:
                var_name = match.group(1)
                self.local_variables[var_name] = 'memory_array'

    def enterForStatement(self, ctx):
        """Track for loop and analyze its condition"""
        if not self.in_function:
            return
        
        self.in_for_loop = True
        self.for_loop_depth += 1
        
        # Get the for loop text
        for_text = ctx.getText()
        self.current_for_line = ctx.start.line
        
        # Extract condition part
        # Pattern: for(init; condition; increment)
        match = re.search(r'for\s*\([^;]*;([^;]*);[^)]*\)', for_text)
        if match:
            condition = match.group(1)
            self.current_for_condition = condition
            
            # Get the body to check for modifications
            self.current_for_body = for_text
            
            # Check if condition uses array.length
            self._check_array_length_in_condition(condition, for_text, ctx.start.line)

    def exitForStatement(self, ctx):
        """Reset for loop context"""
        self.for_loop_depth -= 1
        if self.for_loop_depth == 0:
            self.in_for_loop = False
            self.current_for_condition = None
            self.current_for_body = None
            self.current_for_line = None

    def _check_array_length_in_condition(self, condition, loop_body, line):
        """Check if array.length is used in condition without caching"""
        # Find array.length pattern
        length_matches = re.findall(r'(\w+)\.length', condition)
        
        for array_name in length_matches:
            # Check if it's a storage array (state variable)
            is_storage_array = array_name in self.state_variables
            
            # Check if it's a memory array (less critical)
            is_memory_array = array_name in self.local_variables and \
                            self.local_variables[array_name] == 'memory_array'
            
            # Skip if memory array (lower gas impact)
            if is_memory_array:
                continue
            
            # Skip if not a storage array
            if not is_storage_array:
                continue
            
            # Check if length was already cached
            if array_name in self.cached_lengths:
                continue
            
            # Check if loop modifies the array
            if self._loop_modifies_array(loop_body, array_name):
                continue
            
            # Check if loop has external calls (array might be modified)
            if self._has_external_calls(loop_body):
                continue
            
            # Report the issue
            self.violations.append(
                f"💡 [S-OPT-002] GAS OPTIMIZATION: Cache array length in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                f"Loop condition accesses '{array_name}.length' repeatedly. Cache it in a local variable before the loop to save gas. "
                f"Example: uint length = {array_name}.length; for(uint i = 0; i < length; i++)"
            )

    def _loop_modifies_array(self, loop_body, array_name):
        """Check if loop body modifies the array length"""
        loop_lower = loop_body.lower()
        
        # Check for operations that modify array length
        modifying_operations = [
            f'{array_name}.push',
            f'{array_name}.pop',
            f'delete{array_name}',  # delete entire array
        ]
        
        for op in modifying_operations:
            if op.lower() in loop_lower:
                return True
        
        return False

    def _has_external_calls(self, loop_body):
        """Check if loop has external function calls"""
        # Simple heuristic: look for .call, .delegatecall, or function calls
        external_patterns = [
            r'\.call\(',
            r'\.delegatecall\(',
            r'\.staticcall\(',
            # External contract calls might modify state
        ]
        
        for pattern in external_patterns:
            if re.search(pattern, loop_body):
                return True
        
        return False

    def get_violations(self):
        """Return all detected violations"""
        return self.violations
