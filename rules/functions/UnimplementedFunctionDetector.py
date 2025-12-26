# S-FNC-003: Unimplemented Functions
# Detects functions declared but not implemented
# Indicates abstract contracts or incomplete code

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class UnimplementedFunctionDetector(SolidityParserListener):
    """
    Detects functions that are declared but not implemented.
    
    This detector identifies:
    1. Functions without body (abstract functions)
    2. Functions with empty body that should have implementation
    3. Interface violations
    
    False Positive Mitigation:
    - Excludes abstract contracts (marked as abstract)
    - Excludes interface contracts
    - Excludes virtual functions (intentionally abstract)
    - Only reports non-abstract contracts with unimplemented functions
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.contract_start_line = None
        self.is_abstract = False
        self.is_interface = False
        self.unimplemented_functions = []  # List of (name, line)

    def enterContractDefinition(self, ctx):
        """Track current contract"""
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.contract_start_line = ctx.start.line
        self.unimplemented_functions = []
        
        # Check if abstract or interface
        text = ctx.getText().lower()
        self.is_abstract = 'abstract' in text
        self.is_interface = 'interface' in text

    def exitContractDefinition(self, ctx):
        """Check for violations when exiting contract"""
        # Skip if abstract or interface
        if self.is_abstract or self.is_interface:
            self.current_contract = None
            return
        
        # Report unimplemented functions
        if self.unimplemented_functions:
            for func_name, line in self.unimplemented_functions:
                self.violations.append(
                    f"⚠️  [S-FNC-003] WARNING: Unimplemented function in contract '{self.current_contract}' at line {line}: "
                    f"Function '{func_name}' is declared but not implemented. "
                    f"Either implement the function or mark the contract as abstract."
                )
        
        self.current_contract = None

    def enterFunctionDefinition(self, ctx):
        """Check if function is implemented"""
        func_name = ctx.identifier().getText() if ctx.identifier() else "fallback"
        line = ctx.start.line
        
        # Check if function has a body
        has_body = self._has_function_body(ctx)
        
        # Check if virtual (intentionally abstract)
        is_virtual = 'virtual' in ctx.getText().lower()
        
        # If no body and not virtual, it's unimplemented
        if not has_body and not is_virtual:
            self.unimplemented_functions.append((func_name, line))

    def _has_function_body(self, ctx):
        """Check if function has implementation"""
        text = ctx.getText()
        
        # Check for semicolon without braces (declaration only)
        if ';' in text and '{' not in text:
            return False
        
        # Check for empty body {}
        if '{}' in text.replace(' ', ''):
            return False
        
        # Has braces with content
        if '{' in text and '}' in text:
            # Extract body content
            start = text.find('{')
            end = text.rfind('}')
            body = text[start+1:end].strip()
            
            # If body is empty or only whitespace
            if not body or body.isspace():
                return False
            
            return True
        
        return False

    def get_violations(self):
        """Return all detected violations"""
        return self.violations
