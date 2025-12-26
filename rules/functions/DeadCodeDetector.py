# S-FNC-002: Dead Code Detection
# Detects internal/private functions that are never called
# Increases code complexity and review difficulty

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class DeadCodeDetector(SolidityParserListener):
    """
    Detects unused internal/private functions (dead code).
    
    This detector identifies:
    1. Internal functions never called
    2. Private functions never called
    3. Unused helper functions
    
    False Positive Mitigation:
    - Excludes public/external functions (may be called externally)
    - Excludes constructors, fallback, receive functions
    - Excludes virtual/override functions (may be used in derived contracts)
    - Tracks function calls across the contract
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.functions_defined = {}  # name -> (visibility, line, is_virtual, is_override)
        self.functions_called = set()  # Set of function names called

    def enterContractDefinition(self, ctx):
        """Track current contract"""
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.functions_defined = {}
        self.functions_called = set()

    def exitContractDefinition(self, ctx):
        """Check for dead code when exiting contract"""
        # Check each defined function
        for func_name, (visibility, line, is_virtual, is_override) in self.functions_defined.items():
            # Skip if public/external
            if visibility in ['public', 'external']:
                continue
            
            # Skip if virtual (may be used in derived contracts)
            if is_virtual:
                continue
            
            # Skip if override (part of inheritance hierarchy)
            if is_override:
                continue
            
            # Skip special functions
            if func_name in ['constructor', 'fallback', 'receive']:
                continue
            
            # Check if called
            if func_name not in self.functions_called:
                self.violations.append(
                    f"⚠️  [S-FNC-002] INFO: Dead code in contract '{self.current_contract}' at line {line}: "
                    f"Function '{func_name}' ({visibility}) is never used and should be removed. "
                    f"Dead code increases complexity and makes auditing more difficult."
                )
        
        self.current_contract = None

    def enterFunctionDefinition(self, ctx):
        """Track function definitions"""
        func_name = ctx.identifier().getText() if ctx.identifier() else None
        
        if not func_name:
            # Constructor, fallback, or receive
            func_name = self._get_special_function_name(ctx)
        
        if func_name:
            line = ctx.start.line
            visibility = self._extract_visibility(ctx)
            is_virtual = self._is_virtual(ctx)
            is_override = self._is_override(ctx)
            
            self.functions_defined[func_name] = (visibility, line, is_virtual, is_override)

    def _get_special_function_name(self, ctx):
        """Get name for special functions"""
        text = ctx.getText().lower()
        
        if 'constructor' in text:
            return 'constructor'
        elif 'fallback' in text:
            return 'fallback'
        elif 'receive' in text:
            return 'receive'
        
        return None

    def _extract_visibility(self, ctx):
        """Extract function visibility"""
        text = ctx.getText().lower()
        
        if 'public' in text:
            return 'public'
        elif 'external' in text:
            return 'external'
        elif 'internal' in text:
            return 'internal'
        elif 'private' in text:
            return 'private'
        
        return 'internal'  # Default

    def _is_virtual(self, ctx):
        """Check if function is virtual"""
        return 'virtual' in ctx.getText().lower()

    def _is_override(self, ctx):
        """Check if function is override"""
        return 'override' in ctx.getText().lower()

    def enterStatement(self, ctx):
        """Track function calls"""
        text = ctx.getText()
        
        # Extract function calls (simplified)
        # Look for patterns like: functionName(
        self._extract_function_calls(text)

    def enterExpressionStatement(self, ctx):
        """Track function calls in expressions"""
        text = ctx.getText()
        self._extract_function_calls(text)

    def _extract_function_calls(self, text):
        """Extract function calls from text"""
        import re
        
        # Pattern: word followed by (
        # This is simplified and may have false positives
        pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
        matches = re.findall(pattern, text)
        
        for match in matches:
            # Exclude keywords and common patterns
            if match.lower() not in ['if', 'for', 'while', 'require', 'assert', 'revert', 'emit', 'return']:
                self.functions_called.add(match)

    def get_violations(self):
        """Return all detected violations"""
        return self.violations
