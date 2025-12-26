# S-ERC-002: Incorrect ERC721 Interface
# Detects ERC721 functions with incorrect return types
# Based on Slither's incorrect_erc721_interface detector
# Impact: MEDIUM | Confidence: HIGH

from antlr4 import *
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class IncorrectERC721InterfaceDetector(SolidityParserListener):
    """
    Detects incorrect ERC721 function interfaces.
    
    Vulnerability: ERC721 functions must return specific types. Contracts
    will fail to interact with incorrect implementations.
    
    Expected signatures:
    - balanceOf(address) returns (uint256)
    - ownerOf(uint256) returns (address)
    - safeTransferFrom(address,address,uint256) returns ()
    - transferFrom(address,address,uint256) returns ()
    - approve(address,uint256) returns ()
    - setApprovalForAll(address,bool) returns ()
    - getApproved(uint256) returns (address)
    - isApprovedForAll(address,address) returns (bool)
    - supportsInterface(bytes4) returns (bool)
    
    Recommendation: Use correct return types for ERC721 functions.
    """
    
    def __init__(self):
        self.violations = []
        self.erc721_functions = {}
        self.has_erc721_functions = False
    
    def enterFunctionDefinition(self, ctx):
        func_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        line = ctx.start.line
        
        erc721_funcs = ['balanceOf', 'ownerOf', 'safeTransferFrom', 'transferFrom', 
                        'approve', 'setApprovalForAll', 'getApproved', 'isApprovedForAll',
                        'supportsInterface']
        
        if func_name not in erc721_funcs:
            return
        
        self.has_erc721_functions = True
        
        # Extract params and returns
        params = []
        returns = []
        if ctx.parameterList():
            param_text = ctx.parameterList().getText()
            if 'address' in param_text:
                params.append('address')
            if 'uint256' in param_text:
                params.append('uint256')
            if 'bool' in param_text:
                params.append('bool')
            if 'bytes4' in param_text:
                params.append('bytes4')
        
        if ctx.returnParameters():
            ret_text = ctx.returnParameters().getText()
            if 'address' in ret_text:
                returns.append('address')
            elif 'uint256' in ret_text:
                returns.append('uint256')
            elif 'bool' in ret_text:
                returns.append('bool')
        
        self.erc721_functions[func_name] = (params, returns, line)
    
    def get_violations(self):
        if not self.has_erc721_functions:
            return []
        
        for func_name, (params, returns, line) in self.erc721_functions.items():
            incorrect = False
            expected_return = None
            
            if func_name == 'ownerOf' and 'uint256' in params:
                if 'address' not in returns:
                    incorrect = True
                    expected_return = 'address'
            
            elif func_name == 'balanceOf' and 'address' in params:
                if 'uint256' not in returns:
                    incorrect = True
                    expected_return = 'uint256'
            
            elif func_name == 'getApproved' and 'uint256' in params:
                if 'address' not in returns:
                    incorrect = True
                    expected_return = 'address'
            
            elif func_name == 'isApprovedForAll' and 'address' in params:
                if 'bool' not in returns:
                    incorrect = True
                    expected_return = 'bool'
            
            elif func_name == 'supportsInterface' and 'bytes4' in params:
                if 'bool' not in returns:
                    incorrect = True
                    expected_return = 'bool'
            
            if incorrect:
                self.violations.append(
                    f"❌ [S-ERC-002] Incorrect ERC721 interface at line {line}: "
                    f"Function '{func_name}' should return {expected_return}."
                )
        
        return self.violations
