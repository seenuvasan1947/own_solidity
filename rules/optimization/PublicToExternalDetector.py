# S-OPT-001: Public Function Could Be External
# Detects public functions that could be declared external for gas optimization
# External functions are more gas-efficient when not called internally

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class PublicToExternalDetector(SolidityParserListener):
    """
    Detects public functions that could be declared external.
    
    This detector identifies:
    1. Public functions never called internally
    2. Functions that could save gas by being external
    3. Functions with memory parameters that could use calldata
    
    False Positive Mitigation:
    - Tracks internal function calls
    - Excludes functions called within the contract
    - Excludes virtual functions (may be called in derived contracts)
    - Excludes constructors and special functions
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.public_functions = {}  # name -> (line, has_memory_params)
        self.internal_calls = set()  # Set of internally called function names

    def enterContractDefinition(self, ctx):
        """Track current contract"""
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.public_functions = {}
        self.internal_calls = set()

    def exitContractDefinition(self, ctx):
        """Check for violations when exiting contract"""
        # Check each public function
        for func_name, (line, has_memory_params) in self.public_functions.items():
            # If not called internally, suggest external
            if func_name not in self.internal_calls:
                message = f"⚠️  [S-OPT-001] OPTIMIZATION: Function '{func_name}' in contract '{self.current_contract}' at line {line}: " \
                          f"Public function is never called internally and should be declared external for gas optimization."
                
                if has_memory_params:
                    message += " Additionally, consider changing memory parameters to calldata to save more gas."
                
                self.violations.append(message)
        
        self.current_contract = None

    def enterFunctionDefinition(self, ctx):
        """Track public function definitions"""
        func_name = ctx.identifier().getText() if ctx.identifier() else None
        
        if not func_name:
            return
        
        # Check if public
        text = ctx.getText().lower()
        if 'public' not in text:
            return
        
        # Skip if virtual (may be called in derived contracts)
        if 'virtual' in text:
            return
        
        # Skip if constructor
        if func_name == 'constructor' or 'constructor' in text:
            return
        
        line = ctx.start.line
        has_memory_params = self._has_memory_parameters(ctx)
        
        self.public_functions[func_name] = (line, has_memory_params)

    def _has_memory_parameters(self, ctx):
        """Check if function has memory parameters"""
        text = ctx.getText().lower()
        
        # Check for memory keyword in parameters
        # This is a simplified check
        if 'memory' in text:
            # Make sure it's in parameter context, not just anywhere
            # Look for patterns like: (type memory name)
            return True
        
        return False

    def enterStatement(self, ctx):
        """Track internal function calls"""
        text = ctx.getText()
        self._extract_function_calls(text)

    def enterExpressionStatement(self, ctx):
        """Track function calls in expressions"""
        text = ctx.getText()
        self._extract_function_calls(text)

    def _extract_function_calls(self, text):
        """Extract function calls from text"""
        import re
        
        # Pattern: word followed by (
        pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
        matches = re.findall(pattern, text)
        
        for match in matches:
            # Exclude keywords
            if match.lower() not in ['if', 'for', 'while', 'require', 'assert', 'revert', 'emit', 'return', 'new']:
                # Exclude external calls (contain .)
                if '.' not in text[:text.find(match)]:
                    self.internal_calls.add(match)

    def get_violations(self):
        """Return all detected violations"""
        return self.violations
