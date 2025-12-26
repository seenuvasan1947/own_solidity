# S-ERC-001: Incorrect ERC20 Interface
# Detects ERC20 functions with incorrect return types
# Based on Slither's incorrect_erc20_interface detector
# Impact: MEDIUM | Confidence: HIGH

from antlr4 import *
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class IncorrectERC20InterfaceDetector(SolidityParserListener):
    """
    Detects incorrect ERC20 function interfaces.
    
    Vulnerability: ERC20 functions must return specific types. Contracts
    compiled with Solidity > 0.4.22 will fail to interact with incorrect
    implementations.
    
    Expected signatures:
    - transfer(address,uint256) returns (bool)
    - transferFrom(address,address,uint256) returns (bool)
    - approve(address,uint256) returns (bool)
    - allowance(address,address) returns (uint256)
    - balanceOf(address) returns (uint256)
    - totalSupply() returns (uint256)
    
    Recommendation: Use correct return types for ERC20 functions.
    """
    
    def __init__(self):
        self.violations = []
        self.erc20_functions = {}  # func_name -> (params, returns, line)
        self.has_erc20_functions = False
    
    def enterFunctionDefinition(self, ctx):
        func_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        line = ctx.start.line
        
        # Check if this is an ERC20 function
        if func_name not in ['transfer', 'transferFrom', 'approve', 'allowance', 'balanceOf', 'totalSupply']:
            return
        
        self.has_erc20_functions = True
        
        # Extract parameters
        params = []
        if ctx.parameterList():
            param_list = ctx.parameterList()
            i = 0
            while True:
                param = param_list.parameterDeclaration(i)
                if param is None:
                    break
                param_type = param.typeName().getText() if param.typeName() else "unknown"
                params.append(param_type)
                i += 1
        
        # Extract return type
        returns = []
        if ctx.returnParameters():
            ret_params = ctx.returnParameters().parameterList()
            if ret_params:
                i = 0
                while True:
                    ret_param = ret_params.parameterDeclaration(i)
                    if ret_param is None:
                        break
                    ret_type = ret_param.typeName().getText() if ret_param.typeName() else "unknown"
                    returns.append(ret_type)
                    i += 1
        
        self.erc20_functions[func_name] = (params, returns, line)
    
    def get_violations(self):
        if not self.has_erc20_functions:
            return []
        
        # Check each ERC20 function for correct signature
        for func_name, (params, returns, line) in self.erc20_functions.items():
            incorrect = False
            expected_params = None
            expected_returns = None
            
            if func_name == 'transfer':
                expected_params = ['address', 'uint256']
                expected_returns = ['bool']
                if params == expected_params and returns != expected_returns:
                    incorrect = True
            
            elif func_name == 'transferFrom':
                expected_params = ['address', 'address', 'uint256']
                expected_returns = ['bool']
                if params == expected_params and returns != expected_returns:
                    incorrect = True
            
            elif func_name == 'approve':
                expected_params = ['address', 'uint256']
                expected_returns = ['bool']
                if params == expected_params and returns != expected_returns:
                    incorrect = True
            
            elif func_name == 'allowance':
                expected_params = ['address', 'address']
                expected_returns = ['uint256']
                if params == expected_params and returns != expected_returns:
                    incorrect = True
            
            elif func_name == 'balanceOf':
                expected_params = ['address']
                expected_returns = ['uint256']
                if params == expected_params and returns != expected_returns:
                    incorrect = True
            
            elif func_name == 'totalSupply':
                expected_params = []
                expected_returns = ['uint256']
                if params == expected_params and returns != expected_returns:
                    incorrect = True
            
            if incorrect:
                returns_str = ', '.join(returns) if returns else 'void'
                expected_str = ', '.join(expected_returns)
                self.violations.append(
                    f"❌ [S-ERC-001] Incorrect ERC20 interface at line {line}: "
                    f"Function '{func_name}' returns ({returns_str}) but should return ({expected_str}). "
                    f"Contracts compiled with Solidity > 0.4.22 will fail to interact with this."
                )
        
        return self.violations
