# S-AC-001: Arbitrary Send Ether
# Detects functions that send Ether to arbitrary addresses without proper access control
# Can lead to unauthorized fund withdrawal

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class ArbitrarySendEthDetector(SolidityParserListener):
    """
    Detects functions that send Ether to arbitrary destinations.
    
    This detector identifies:
    1. Functions sending Ether to user-controlled addresses
    2. Transfer/send/call operations without proper access control
    3. Withdrawal functions accessible by arbitrary users
    
    False Positive Mitigation:
    - Excludes functions with access control modifiers (onlyOwner, etc.)
    - Excludes withdraw patterns where msg.sender is used as index
    - Excludes repay patterns where msg.value is sent
    - Excludes functions with transferFrom calls
    - Checks for ecrecover usage (signature validation)
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None
        self.function_start_line = None
        self.function_modifiers = []
        self.has_access_control = False
        self.uses_msg_sender_index = False
        self.uses_msg_value = False
        self.has_ecrecover = False
        self.has_transfer_from = False
        self.ether_sends = []  # Track ether send operations

    def enterContractDefinition(self, ctx):
        """Track current contract"""
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"

    def exitContractDefinition(self, ctx):
        """Reset contract context"""
        self.current_contract = None

    def enterFunctionDefinition(self, ctx):
        """Analyze function for arbitrary send patterns"""
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "fallback"
        self.function_start_line = ctx.start.line
        self.function_modifiers = []
        self.has_access_control = False
        self.uses_msg_sender_index = False
        self.uses_msg_value = False
        self.has_ecrecover = False
        self.has_transfer_from = False
        self.ether_sends = []
        
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
                                
                                # Check for access control modifiers
                                if any(ac in mod_name for ac in ['onlyowner', 'onlyadmin', 'authorized', 'restricted']):
                                    self.has_access_control = True
        except Exception:
            pass

    def enterStatement(self, ctx):
        """Check statements for ether sends and patterns"""
        if not self.in_function:
            return
        
        line = ctx.start.line
        text = ctx.getText()
        
        # Check for ecrecover (signature validation)
        if 'ecrecover(' in text.lower():
            self.has_ecrecover = True
        
        # Check for transferFrom (ERC20 pattern)
        if 'transferfrom(' in text.lower():
            self.has_transfer_from = True
        
        # Check for msg.sender used as index (withdraw pattern)
        if self._is_msg_sender_index(text):
            self.uses_msg_sender_index = True
        
        # Check for ether send operations
        self._check_ether_send(text, line)

    def _is_msg_sender_index(self, text):
        """Check if msg.sender is used as array/mapping index"""
        text_lower = text.lower()
        
        # Pattern: balances[msg.sender] or similar
        if 'msg.sender]' in text_lower:
            return True
        
        # Pattern: mapping access with msg.sender
        if '[msg.sender' in text_lower:
            return True
        
        return False

    def _check_ether_send(self, text, line):
        """Check for ether send operations"""
        text_lower = text.lower()
        
        # Check for transfer/send/call with value
        ether_send_patterns = [
            '.transfer(', '.send(', 
            '.call{value:', 'call.value('
        ]
        
        for pattern in ether_send_patterns:
            if pattern in text_lower:
                # Check if sending msg.value (repay pattern - safe)
                if 'msg.value' in text_lower:
                    self.uses_msg_value = True
                else:
                    # Extract destination address (simplified)
                    self.ether_sends.append((line, text[:100]))
                break

    def exitFunctionDefinition(self, ctx):
        """Check for violations when exiting function"""
        # Skip if no ether sends
        if not self.ether_sends:
            self.in_function = False
            return
        
        # Skip if has access control
        if self.has_access_control:
            self.in_function = False
            return
        
        # Skip if uses msg.sender as index (withdraw pattern)
        if self.uses_msg_sender_index:
            self.in_function = False
            return
        
        # Skip if uses msg.value (repay pattern)
        if self.uses_msg_value:
            self.in_function = False
            return
        
        # Skip if has ecrecover (signature validation)
        if self.has_ecrecover:
            self.in_function = False
            return
        
        # Skip if has transferFrom (ERC20 pattern)
        if self.has_transfer_from:
            self.in_function = False
            return
        
        # Report violations
        for line, send_text in self.ether_sends:
            self.violations.append(
                f"❌ [S-AC-001] CRITICAL: Arbitrary send Ether in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                f"Function sends Ether to arbitrary address without proper access control. "
                f"Add access control modifiers or ensure the destination is validated."
            )
        
        self.in_function = False

    def get_violations(self):
        """Return all detected violations"""
        return self.violations
