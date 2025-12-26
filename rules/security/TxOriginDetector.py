# S-SEC-011: Dangerous tx.origin Usage
# Detects use of tx.origin for authorization which can be exploited via phishing
# tx.origin should not be used for access control

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class TxOriginDetector(SolidityParserListener):
    """
    Detects dangerous usage of tx.origin for authorization.
    
    This detector identifies:
    1. tx.origin used in require/assert statements
    2. tx.origin used in if conditions for access control
    3. tx.origin comparisons without msg.sender validation
    
    False Positive Mitigation:
    - Excludes cases where tx.origin == msg.sender (legitimate check)
    - Excludes informational/logging usage
    - Focuses on authorization contexts (require, assert, if with revert)
    - Allows tx.origin in non-critical contexts
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None
        self.function_start_line = None

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

    def exitFunctionDefinition(self, ctx):
        """Reset function context"""
        self.in_function = False
        self.function_name = None

    def enterStatement(self, ctx):
        """Check statements for tx.origin usage"""
        if not self.in_function:
            return
        
        line = ctx.start.line
        text = ctx.getText()
        
        self._check_tx_origin_usage(text, line)

    def enterExpressionStatement(self, ctx):
        """Check expression statements for tx.origin"""
        if not self.in_function:
            return
        
        line = ctx.start.line
        text = ctx.getText()
        
        self._check_tx_origin_usage(text, line)

    def _check_tx_origin_usage(self, text, line):
        """Check if text contains dangerous tx.origin usage"""
        text_lower = text.lower()
        
        # Check if tx.origin is used
        if 'tx.origin' not in text_lower:
            return
        
        # Check if it's a legitimate check (tx.origin == msg.sender)
        if self._is_legitimate_check(text_lower):
            return
        
        # Check if used in authorization context
        is_in_require = 'require(' in text_lower
        is_in_assert = 'assert(' in text_lower
        is_in_if = 'if(' in text_lower or 'if (' in text_lower
        
        # Check for comparison operators (authorization check)
        has_comparison = '==' in text or '!=' in text
        
        if (is_in_require or is_in_assert) and has_comparison:
            # High confidence - tx.origin in require/assert
            self.violations.append(
                f"❌ [S-SEC-011] CRITICAL: Dangerous tx.origin usage in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                f"Using tx.origin for authorization can be exploited via phishing attacks. Use msg.sender instead."
            )
        elif is_in_if and has_comparison:
            # Medium confidence - tx.origin in if condition
            # Check if it's likely an authorization check
            if self._is_authorization_context(text_lower):
                self.violations.append(
                    f"⚠️  [S-SEC-011] WARNING: Potential dangerous tx.origin usage in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                    f"Using tx.origin in conditional logic for authorization is unsafe. Use msg.sender instead."
                )

    def _is_legitimate_check(self, text):
        """Check if this is a legitimate tx.origin == msg.sender check"""
        # Pattern: tx.origin == msg.sender or msg.sender == tx.origin
        patterns = [
            'tx.origin==msg.sender',
            'msg.sender==tx.origin',
            'tx.origin!=msg.sender',
            'msg.sender!=tx.origin'
        ]
        
        text_no_space = text.replace(' ', '')
        return any(pattern in text_no_space for pattern in patterns)

    def _is_authorization_context(self, text):
        """Check if the context suggests authorization"""
        auth_indicators = [
            'owner', 'admin', 'authorized', 'allowed',
            'revert', 'throw', 'access', 'permission'
        ]
        
        return any(indicator in text for indicator in auth_indicators)

    def get_violations(self):
        """Return all detected violations"""
        return self.violations
