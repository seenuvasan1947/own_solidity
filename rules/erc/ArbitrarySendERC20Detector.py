# S-ERC-004: Arbitrary Send ERC20 (General)
# Detects transferFrom with arbitrary 'from' address
# Based on Slither's arbitrary_send_erc20 detector
# Impact: MEDIUM | Confidence: MEDIUM

from antlr4 import *
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class ArbitrarySendERC20Detector(SolidityParserListener):
    """
    Detects transferFrom with arbitrary 'from' address.
    
    Vulnerability: Using transferFrom with a user-controlled 'from'
    parameter allows attackers to transfer tokens from any address
    that approved the contract.
    
    Example (BAD):
        function transfer(address from, address to, uint256 amount) public {
            token.transferFrom(from, to, amount);  // BAD: arbitrary 'from'
        }
    
    Example (GOOD):
        function transfer(address to, uint256 amount) public {
            token.transferFrom(msg.sender, to, amount);  // GOOD: uses msg.sender
        }
    
    Recommendation: Use msg.sender or address(this) as 'from' parameter.
    """
    
    def __init__(self):
        self.violations = []
        self.in_function = False
        self.function_name = None
    
    def enterFunctionDefinition(self, ctx):
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
    
    def exitFunctionDefinition(self, ctx):
        self.in_function = False
    
    def enterExpressionStatement(self, ctx):
        if not self.in_function:
            return
        
        text = ctx.getText()
        line = ctx.start.line
        
        # Check for transferFrom without msg.sender check
        if 'transferFrom(' in text or '.safeTransferFrom(' in text:
            # Check if msg.sender or address(this) is used
            if 'msg.sender' not in text and 'address(this)' not in text:
                self.violations.append(
                    f"⚠️ [S-ERC-004] Arbitrary send ERC20 at line {line}: "
                    f"transferFrom() call with potentially arbitrary 'from' address. "
                    f"Attacker may transfer tokens from any address that approved this contract. "
                    f"Use msg.sender or address(this) as 'from' parameter."
                )
    
    def get_violations(self):
        return self.violations
