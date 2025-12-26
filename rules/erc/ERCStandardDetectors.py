# S-ERC-002: Incorrect ERC721 Interface
# S-ERC-003: Unindexed ERC20 Event Parameters  
# S-ERC-004: Arbitrary Send ERC20
# Combined implementation for efficiency

from antlr4 import *
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

# S-ERC-002: Incorrect ERC721 Interface
class IncorrectERC721InterfaceDetector(SolidityParserListener):
    """Detects incorrect ERC721 function interfaces."""
    
    def __init__(self):
        self.violations = []
        self.erc721_functions = {}
        self.has_erc721_functions = False
    
    def enterFunctionDefinition(self, ctx):
        func_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        line = ctx.start.line
        
        erc721_funcs = ['balanceOf', 'ownerOf', 'safeTransferFrom', 'transferFrom', 
                        'approve', 'setApprovalForAll', 'getApproved', 'isApprovedForAll']
        
        if func_name not in erc721_funcs:
            return
        
        self.has_erc721_functions = True
        
        # Extract params and returns (simplified)
        params = []
        returns = []
        if ctx.parameterList():
            param_text = ctx.parameterList().getText()
            if 'address' in param_text:
                params.append('address')
            if 'uint256' in param_text:
                params.append('uint256')
        
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
            
            if func_name == 'ownerOf' and 'uint256' in params and 'address' not in returns:
                incorrect = True
            elif func_name == 'balanceOf' and 'address' in params and 'uint256' not in returns:
                incorrect = True
            
            if incorrect:
                self.violations.append(
                    f"❌ [S-ERC-002] Incorrect ERC721 interface at line {line}: "
                    f"Function '{func_name}' has wrong return type."
                )
        
        return self.violations


# S-ERC-003: Unindexed ERC20 Event Parameters
class UnindexedERC20EventDetector(SolidityParserListener):
    """Detects ERC20 events without indexed parameters."""
    
    def __init__(self):
        self.violations = []
    
    def enterEventDefinition(self, ctx):
        event_name = ctx.identifier(0).getText() if ctx.identifier(0) else "unknown"
        line = ctx.start.line
        
        if event_name not in ['Transfer', 'Approval']:
            return
        
        # Check if parameters are indexed
        event_text = ctx.getText()
        
        if event_name == 'Transfer' or event_name == 'Approval':
            # Count indexed keywords
            indexed_count = event_text.count('indexed')
            
            if indexed_count < 2:
                self.violations.append(
                    f"⚠️ [S-ERC-003] Unindexed ERC20 event parameters at line {line}: "
                    f"Event '{event_name}' should have first two parameters indexed for proper filtering."
                )
    
    def get_violations(self):
        return self.violations


# S-ERC-004: Arbitrary Send ERC20
class ArbitrarySendERC20Detector(SolidityParserListener):
    """Detects transferFrom with arbitrary 'from' address."""
    
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
        if 'transferFrom(' in text:
            # Simple heuristic: if transferFrom is used but msg.sender is not in the same statement
            if 'msg.sender' not in text and 'address(this)' not in text:
                self.violations.append(
                    f"⚠️ [S-ERC-004] Arbitrary send ERC20 at line {line}: "
                    f"transferFrom() call with potentially arbitrary 'from' address. "
                    f"Ensure proper authorization checks."
                )
    
    def get_violations(self):
        return self.violations
