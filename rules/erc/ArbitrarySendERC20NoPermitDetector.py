# S-ERC-005: Arbitrary Send ERC20 (No Permit)
# Detects transferFrom with arbitrary 'from' without permit
# Based on Slither's arbitrary_send_erc20_no_permit detector
# Impact: HIGH | Confidence: HIGH

from antlr4 import *
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class ArbitrarySendERC20NoPermitDetector(SolidityParserListener):
    """
    Detects transferFrom with arbitrary 'from' without permit.
    
    Vulnerability: Critical security issue where transferFrom uses
    an arbitrary 'from' parameter without permit protection.
    
    Example (BAD):
        function transfer(address from, address to, uint256 amount) public {
            erc20.transferFrom(from, to, amount);  // CRITICAL: arbitrary 'from'
        }
    
    Attack: Alice approves contract for 100 tokens. Bob calls transfer()
    with from=Alice, to=Bob, stealing Alice's tokens.
    
    Recommendation: Use msg.sender as 'from' parameter.
    """
    
    def __init__(self):
        self.violations = []
        self.in_function = False
        self.function_has_permit = False
        self.function_name = None
    
    def enterFunctionDefinition(self, ctx):
        self.in_function = True
        self.function_has_permit = False
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
    
    def exitFunctionDefinition(self, ctx):
        self.in_function = False
    
    def enterExpressionStatement(self, ctx):
        if not self.in_function:
            return
        
        text = ctx.getText()
        line = ctx.start.line
        
        # Check for permit calls
        if '.permit(' in text:
            self.function_has_permit = True
        
        # Check for transferFrom without msg.sender and without permit
        if '.transferFrom(' in text:
            if 'msg.sender' not in text and 'address(this)' not in text and not self.function_has_permit:
                self.violations.append(
                    f"❌ [S-ERC-005] Arbitrary send ERC20 (no permit) at line {line}: "
                    f"transferFrom() uses arbitrary 'from' parameter without permit protection. "
                    f"CRITICAL: Attacker can steal tokens from any address that approved this contract. "
                    f"Use msg.sender as 'from' parameter."
                )
    
    def get_violations(self):
        return self.violations
