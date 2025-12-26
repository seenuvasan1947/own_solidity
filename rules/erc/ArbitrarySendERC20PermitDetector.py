# S-ERC-006: Arbitrary Send ERC20 (With Permit)
# Detects transferFrom with arbitrary 'from' when permit is used
# Based on Slither's arbitrary_send_erc20_permit detector
# Impact: HIGH | Confidence: MEDIUM

from antlr4 import *
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class ArbitrarySendERC20PermitDetector(SolidityParserListener):
    """
    Detects transferFrom with arbitrary 'from' when permit is used.
    
    Vulnerability: Using permit with transferFrom and arbitrary 'from'
    can allow attackers to drain tokens if the ERC20 doesn't properly
    implement permit (e.g., WETH with fallback function).
    
    Example (BAD):
        function bad(address from, uint256 value, uint256 deadline, 
                     uint8 v, bytes32 r, bytes32 s, address to) public {
            erc20.permit(from, address(this), value, deadline, v, r, s);
            erc20.transferFrom(from, to, value);  // Risky with permit
        }
    
    Attack: If ERC20 doesn't implement permit but has fallback (like WETH),
    the permit call succeeds silently, and transferFrom drains approved tokens.
    
    Recommendation: Ensure underlying ERC20 correctly implements permit,
    or verify permit success before transferFrom.
    """
    
    def __init__(self):
        self.violations = []
        self.in_function = False
        self.function_has_permit = False
        self.function_has_transferfrom = False
        self.function_name = None
        self.function_line = None
    
    def enterFunctionDefinition(self, ctx):
        self.in_function = True
        self.function_has_permit = False
        self.function_has_transferfrom = False
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.function_line = ctx.start.line
    
    def exitFunctionDefinition(self, ctx):
        # Check if both permit and transferFrom are used
        if self.function_has_permit and self.function_has_transferfrom:
            self.violations.append(
                f"❌ [S-ERC-006] Arbitrary send ERC20 with permit at line {self.function_line}: "
                f"Function '{self.function_name}' uses permit() with transferFrom() and arbitrary 'from'. "
                f"If ERC20 doesn't implement permit correctly (e.g., WETH with fallback), "
                f"attacker can drain all approved tokens. Verify ERC20 implementation or check permit return value."
            )
        
        self.in_function = False
    
    def enterExpressionStatement(self, ctx):
        if not self.in_function:
            return
        
        text = ctx.getText()
        
        if '.permit(' in text:
            self.function_has_permit = True
        
        if '.transferFrom(' in text and 'msg.sender' not in text and 'address(this)' not in text:
            self.function_has_transferfrom = True
    
    def get_violations(self):
        return self.violations
