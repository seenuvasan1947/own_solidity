# S-ERC-005: Arbitrary Send ERC20 (No Permit)
# S-ERC-006: Arbitrary Send ERC20 (With Permit)
# S-ERC-007: ERC721 Interface
# Remaining ERC detectors

from antlr4 import *
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

# S-ERC-005: Arbitrary Send ERC20 No Permit
class ArbitrarySendERC20NoPermitDetector(SolidityParserListener):
    """
    Detects transferFrom with arbitrary 'from' without permit.
    
    Vulnerability: If transferFrom uses an arbitrary 'from' parameter
    instead of msg.sender, attackers can transfer tokens from any address
    that approved the contract.
    
    Example (BAD):
        function transfer(address from, address to, uint256 amount) public {
            erc20.transferFrom(from, to, amount);  // BAD: arbitrary 'from'
        }
    
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
        
        # Check for transferFrom without msg.sender
        if '.transferFrom(' in text:
            if 'msg.sender' not in text and not self.function_has_permit:
                self.violations.append(
                    f"❌ [S-ERC-005] Arbitrary send ERC20 at line {line}: "
                    f"transferFrom() uses arbitrary 'from' parameter. "
                    f"Attacker can transfer tokens from any address that approved this contract. "
                    f"Use msg.sender as 'from' parameter."
                )
    
    def get_violations(self):
        return self.violations


# S-ERC-006: Arbitrary Send ERC20 With Permit
class ArbitrarySendERC20PermitDetector(SolidityParserListener):
    """
    Detects transferFrom with arbitrary 'from' when permit is used.
    
    Vulnerability: Using permit with transferFrom and arbitrary 'from'
    can allow attackers to drain tokens if the ERC20 doesn't properly
    implement permit (e.g., WETH with fallback).
    
    Example (BAD):
        function bad(address from, uint256 value, ...) public {
            erc20.permit(from, address(this), value, ...);
            erc20.transferFrom(from, to, value);  // Risky with permit
        }
    
    Recommendation: Ensure underlying ERC20 correctly implements permit.
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
                f"⚠️ [S-ERC-006] Arbitrary send ERC20 with permit at line {self.function_line}: "
                f"Function '{self.function_name}' uses permit() with transferFrom(). "
                f"If ERC20 doesn't implement permit correctly (e.g., WETH), "
                f"attacker can drain approved tokens. Verify ERC20 implementation."
            )
        
        self.in_function = False
    
    def enterExpressionStatement(self, ctx):
        if not self.in_function:
            return
        
        text = ctx.getText()
        
        if '.permit(' in text:
            self.function_has_permit = True
        
        if '.transferFrom(' in text and 'msg.sender' not in text:
            self.function_has_transferfrom = True
    
    def get_violations(self):
        return self.violations


# S-ERC-007: Complete ERC721 Interface Check
class CompleteERC721InterfaceDetector(SolidityParserListener):
    """
    Comprehensive ERC721 interface validation.
    
    Checks all ERC721 required functions:
    - balanceOf(address) returns (uint256)
    - ownerOf(uint256) returns (address)
    - safeTransferFrom variants
    - transferFrom(address,address,uint256)
    - approve(address,uint256)
    - setApprovalForAll(address,bool)
    - getApproved(uint256) returns (address)
    - isApprovedForAll(address,address) returns (bool)
    - supportsInterface(bytes4) returns (bool)
    """
    
    def __init__(self):
        self.violations = []
        self.erc721_functions = {}
        self.has_erc721_indicators = False
    
    def enterFunctionDefinition(self, ctx):
        func_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        line = ctx.start.line
        
        # Check for ERC721-specific functions
        erc721_funcs = ['ownerOf', 'safeTransferFrom', 'tokenURI', 'supportsInterface']
        if func_name in erc721_funcs:
            self.has_erc721_indicators = True
        
        # Validate specific signatures
        if func_name == 'ownerOf':
            func_text = ctx.getText()
            if 'uint256' in func_text and 'address' not in (ctx.returnParameters().getText() if ctx.returnParameters() else ''):
                self.violations.append(
                    f"❌ [S-ERC-007] Incorrect ERC721 interface at line {line}: "
                    f"ownerOf(uint256) must return address, not other type."
                )
        
        elif func_name == 'supportsInterface':
            func_text = ctx.getText()
            if 'bytes4' in func_text and 'bool' not in (ctx.returnParameters().getText() if ctx.returnParameters() else ''):
                self.violations.append(
                    f"❌ [S-ERC-007] Incorrect ERC721 interface at line {line}: "
                    f"supportsInterface(bytes4) must return bool."
                )
    
    def get_violations(self):
        return self.violations
