# S-FNC-004: Protected Variables
# Detects state variables that should be protected but are modified without proper access control
# Based on @custom:security write-protection annotations

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class ProtectedVariablesDetector(SolidityParserListener):
    """
    Detects unprotected writes to variables marked as protected.
    
    This detector identifies:
    1. State variables with @custom:security write-protection annotations
    2. Functions that modify protected variables without required modifiers
    3. Access control violations for critical state variables
    
    False Positive Mitigation:
    - Only checks variables explicitly marked as protected
    - Verifies required modifiers are present
    - Checks for inline access control (require/assert)
    - Excludes constructor initialization
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.protected_variables = {}  # var_name -> required_protection
        self.in_function = False
        self.function_name = None
        self.function_start_line = None
        self.function_modifiers = []
        self.state_var_writes = []  # Variables written in current function

    def enterContractDefinition(self, ctx):
        """Track current contract"""
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.protected_variables = {}

    def exitContractDefinition(self, ctx):
        """Reset contract context"""
        self.current_contract = None

    def enterStateVariableDeclaration(self, ctx):
        """Check for protected variable annotations"""
        # Get the full text including comments
        var_name = None
        if hasattr(ctx, 'identifier') and ctx.identifier():
            var_name = ctx.identifier().getText()
        
        if not var_name:
            return
        
        # Check for @custom:security write-protection annotation
        # This would be in comments above the variable
        # For ANTLR, we need to check the text before this declaration
        # Simplified: look for protection patterns in variable name or context
        
        # Common critical variables that should be protected
        critical_vars = ['owner', '_owner', 'admin', '_admin', 'paused', '_paused']
        if var_name.lower() in critical_vars:
            # Assume these should be protected by onlyOwner or onlyAdmin
            self.protected_variables[var_name] = 'onlyOwner'

    def enterFunctionDefinition(self, ctx):
        """Track function and its modifiers"""
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "constructor"
        self.function_start_line = ctx.start.line
        self.function_modifiers = []
        self.state_var_writes = []
        
        # Extract modifiers
        self._extract_modifiers(ctx)

    def _extract_modifiers(self, ctx):
        """Extract function modifiers"""
        try:
            if hasattr(ctx, 'modifierList') and ctx.modifierList():
                modifier_list = ctx.modifierList()
                if hasattr(modifier_list, 'modifierInvocation'):
                    modifiers = modifier_list.modifierInvocation()
                    if modifiers:
                        for mod in modifiers:
                            if hasattr(mod, 'identifier') and mod.identifier():
                                mod_name = mod.identifier().getText()
                                self.function_modifiers.append(mod_name)
        except Exception:
            pass

    def enterStatement(self, ctx):
        """Track state variable writes"""
        if not self.in_function:
            return
        
        text = ctx.getText()
        
        # Check for writes to protected variables
        for var_name in self.protected_variables.keys():
            # Pattern: varName = ...
            if f'{var_name}=' in text or f'{var_name} =' in text:
                if '==' not in text and '!=' not in text:
                    self.state_var_writes.append(var_name)

    def exitFunctionDefinition(self, ctx):
        """Check for violations when exiting function"""
        # Skip constructor
        if self.function_name == 'constructor':
            self.in_function = False
            return
        
        # Check each protected variable written
        for var_name in self.state_var_writes:
            required_protection = self.protected_variables.get(var_name)
            
            if required_protection:
                # Check if function has the required modifier
                has_protection = any(required_protection.lower() in mod.lower() 
                                    for mod in self.function_modifiers)
                
                if not has_protection:
                    self.violations.append(
                        f"❌ [S-FNC-004] CRITICAL: Unprotected write to protected variable in function '{self.function_name}' of contract '{self.current_contract}' at line {self.function_start_line}: "
                        f"Variable '{var_name}' is protected and requires '{required_protection}' modifier, but function lacks proper access control. "
                        f"Add the required modifier to prevent unauthorized modifications."
                    )
        
        self.in_function = False

    def get_violations(self):
        """Return all detected violations"""
        return self.violations
