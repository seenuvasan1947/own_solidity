from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class InsufficientAuthorizationDetector(SolidityParserListener):
    """
    Detector for SCWE-016: Insufficient Authorization Checks
    Rule Code: 016
    
    Detects functions that lack proper authorization checks for sensitive operations.
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.current_function = None
        self.contract_functions = {}  # contract_name -> list of function info
        self.sensitive_functions = {}  # contract_name -> list of sensitive functions
        self.authorization_patterns = {}  # contract_name -> set of auth patterns
        
        # Sensitive function keywords that require authorization
        self.sensitive_keywords = [
            'withdraw', 'transfer', 'mint', 'burn', 'pause', 'unpause',
            'upgrade', 'set', 'update', 'change', 'modify', 'configure',
            'approve', 'revoke', 'grant', 'remove', 'delete', 'destroy',
            'emergency', 'admin', 'owner', 'governance', 'treasury'
        ]
        
        # Authorization patterns
        self.auth_patterns = [
            'onlyOwner', 'onlyAdmin', 'onlyGovernance', 'onlyRole',
            'require(msg.sender == owner)', 'require(msg.sender == admin)',
            'require(msg.sender==owner)', 'require(msg.sender==admin)',
            'require(hasRole(', 'require(isOwner(', 'require(isAdmin(',
            'require(msg.sender ==', 'require(msg.sender==',
            'require(owner == msg.sender)', 'require(admin == msg.sender)',
            'require(owner==msg.sender)', 'require(admin==msg.sender)',
            'require(governor == msg.sender)', 'require(governor==msg.sender)',
            'require(msg.sender == owner', 'require(msg.sender == admin',
            'require(msg.sender==owner', 'require(msg.sender==admin',
            'require(owner == msg.sender', 'require(admin == msg.sender',
            'require(owner==msg.sender', 'require(admin==msg.sender'
        ]
        
        # Functions that are typically public and don't need authorization
        self.public_functions = [
            'get', 'view', 'read', 'check', 'is', 'has', 'can', 'balance',
            'totalSupply', 'name', 'symbol', 'decimals', 'owner', 'admin'
        ]
    
    def enterContractDefinition(self, ctx):
        """Track contract definitions and initialize data structures."""
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "UnknownContract"
        self.contract_functions[self.current_contract] = []
        self.sensitive_functions[self.current_contract] = []
        self.authorization_patterns[self.current_contract] = set()
    
    def exitContractDefinition(self, ctx):
        """Analyze authorization after processing the contract."""
        if self.current_contract:
            self._analyze_authorization()
        self.current_contract = None
    
    def enterFunctionDefinition(self, ctx):
        """Track function definitions and analyze sensitive functions."""
        if not self.current_contract:
            return
            
        func_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.current_function = func_name
        
        # Check if this is a sensitive function
        is_sensitive = self._is_sensitive_function(func_name)
        
        # Check for authorization patterns in function
        has_auth_modifier = False
        has_auth_require = False
        
        # Check modifiers
        for child in ctx.children:
            if hasattr(child, 'getText'):
                modifier_text = child.getText()
                if any(pattern in modifier_text for pattern in ['onlyOwner', 'onlyAdmin', 'onlyGovernance', 'onlyRole']):
                    has_auth_modifier = True
                    break
        
        function_info = {
            'name': func_name,
            'line': ctx.start.line,
            'is_sensitive': is_sensitive,
            'has_auth_modifier': has_auth_modifier,
            'has_auth_require': has_auth_require,
            'visibility': self._get_function_visibility(ctx)
        }
        
        self.contract_functions[self.current_contract].append(function_info)
        
        if is_sensitive:
            self.sensitive_functions[self.current_contract].append(function_info)
    
    def exitFunctionDefinition(self, ctx):
        """Clear current function when exiting function definition."""
        self.current_function = None
    
    def enterExpressionStatement(self, ctx):
        """Check for authorization patterns in function bodies."""
        if not self.current_function or not self.current_contract:
            return
            
        expr_text = ctx.getText()
        
        # Check for authorization patterns
        for pattern in self.auth_patterns:
            if pattern in expr_text:
                self.authorization_patterns[self.current_contract].add(pattern)
                # Mark current function as having auth require
                for func in self.contract_functions[self.current_contract]:
                    if func['name'] == self.current_function:
                        func['has_auth_require'] = True
                        break
                break
    
    def _is_sensitive_function(self, func_name):
        """Check if function name suggests sensitive operations."""
        func_lower = func_name.lower()
        
        # Skip public getter functions
        if any(public_func in func_lower for public_func in self.public_functions):
            return False
        
        # Check for sensitive keywords
        return any(keyword in func_lower for keyword in self.sensitive_keywords)
    
    def _get_function_visibility(self, ctx):
        """Get function visibility (public, external, internal, private)."""
        for child in ctx.children:
            if hasattr(child, 'getText'):
                text = child.getText()
                if text in ['public', 'external', 'internal', 'private']:
                    return text
        return 'public'  # Default visibility
    
    def _analyze_authorization(self):
        """Analyze authorization for sensitive functions."""
        if not self.current_contract:
            return
        
        sensitive_funcs = self.sensitive_functions.get(self.current_contract, [])
        
        # Check each sensitive function for proper authorization
        for func in sensitive_funcs:
            if not func['has_auth_modifier'] and not func['has_auth_require']:
                # Skip if function is internal or private (they have implicit access control)
                if func['visibility'] in ['internal', 'private']:
                    continue
                
                violation = {
                    'type': 'SCWE-016',
                    'contract': self.current_contract,
                    'function': func['name'],
                    'line': func['line'],
                    'message': f"Function '{func['name']}' lacks proper authorization checks for sensitive operation"
                }
                self.violations.append(violation)
    
    def get_violations(self):
        """Return list of detected violations."""
        return self.violations
