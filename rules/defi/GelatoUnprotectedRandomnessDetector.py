# S-DEFI-001: Gelato Unprotected Randomness
# Detects unprotected calls to Gelato VRF randomness requests
# Can be exploited by unauthorized users

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class GelatoUnprotectedRandomnessDetector(SolidityParserListener):
    """
    Detects unprotected Gelato VRF randomness requests.
    
    This detector identifies:
    1. Calls to _requestRandomness without access control
    2. Public/external functions requesting randomness
    3. Gelato VRF consumer contracts with unprotected requests
    
    False Positive Mitigation:
    - Only checks contracts inheriting from GelatoVRFConsumerBase
    - Checks for access control modifiers
    - Excludes protected functions
    - Verifies actual randomness request calls
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.is_gelato_consumer = False
        self.in_function = False
        self.function_name = None
        self.function_start_line = None
        self.function_modifiers = []
        self.has_access_control = False
        self.randomness_requests = []  # Lines where randomness is requested

    def enterContractDefinition(self, ctx):
        """Track current contract"""
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.is_gelato_consumer = False
        
        # Check if inherits from GelatoVRFConsumerBase
        text = ctx.getText()
        if 'GelatoVRFConsumerBase' in text or 'GelatoVRF' in text:
            self.is_gelato_consumer = True

    def exitContractDefinition(self, ctx):
        """Reset contract context"""
        self.current_contract = None

    def enterFunctionDefinition(self, ctx):
        """Track function"""
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "fallback"
        self.function_start_line = ctx.start.line
        self.function_modifiers = []
        self.has_access_control = False
        self.randomness_requests = []
        
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
                                mod_name = mod.identifier().getText().lower()
                                self.function_modifiers.append(mod_name)
                                
                                # Check for access control
                                if any(ac in mod_name for ac in ['onlyowner', 'onlyadmin', 'authorized', 'restricted']):
                                    self.has_access_control = True
        except Exception:
            pass

    def enterStatement(self, ctx):
        """Check for randomness requests"""
        if not self.in_function or not self.is_gelato_consumer:
            return
        
        text = ctx.getText()
        line = ctx.start.line
        
        # Check for _requestRandomness call
        if '_requestRandomness(' in text or '_requestRandomness (' in text:
            self.randomness_requests.append(line)

    def exitFunctionDefinition(self, ctx):
        """Check for violations"""
        if not self.is_gelato_consumer or not self.randomness_requests:
            self.in_function = False
            return
        
        # If function requests randomness without access control
        if not self.has_access_control:
            for line in self.randomness_requests:
                self.violations.append(
                    f"⚠️  [S-DEFI-001] WARNING: Unprotected Gelato VRF randomness request in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                    f"Function requests randomness without access control. Unauthorized users can trigger randomness requests. "
                    f"Add access control modifiers (onlyOwner, onlyAuthorized, etc.)."
                )
        
        self.in_function = False

    def get_violations(self):
        """Return all detected violations"""
        return self.violations
