from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class PrivilegedRoleMismanagementDetector(SolidityParserListener):
    """
    Detector for SCWE-017: Privileged Role Mismanagement
    Rule Code: 017
    
    Detects functions that allow unauthorized role assignment or privilege escalation.
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.current_function = None
        self.contract_functions = {}  # contract_name -> list of function info
        self.role_functions = {}  # contract_name -> list of role management functions
        self.role_variables = {}  # contract_name -> list of role variables
        
        # Role management function keywords
        self.role_keywords = [
            'set', 'assign', 'grant', 'add', 'remove', 'revoke', 'delete',
            'admin', 'owner', 'governor', 'role', 'permission', 'authority'
        ]
        
        # Authorization patterns for role management
        self.role_auth_patterns = [
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
        
        # Role variable patterns
        self.role_variable_patterns = [
            'owner', 'admin', 'governor', 'authority', 'controller',
            'manager', 'operator', 'guardian', 'treasury'
        ]
    
    def enterContractDefinition(self, ctx):
        """Track contract definitions and initialize data structures."""
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "UnknownContract"
        self.contract_functions[self.current_contract] = []
        self.role_functions[self.current_contract] = []
        self.role_variables[self.current_contract] = []
    
    def exitContractDefinition(self, ctx):
        """Analyze role management after processing the contract."""
        if self.current_contract:
            self._analyze_role_management()
        self.current_contract = None
    
    def enterStateVariableDeclaration(self, ctx):
        """Track role-related state variables."""
        if not self.current_contract:
            return
            
        var_name = ctx.identifier().getText() if ctx.identifier() else ""
        var_type = ctx.typeName().getText() if ctx.typeName() else ""
        
        # Check if this is a role variable
        if any(pattern in var_name.lower() for pattern in self.role_variable_patterns):
            self.role_variables[self.current_contract].append({
                'name': var_name,
                'type': var_type,
                'line': ctx.start.line
            })
    
    def enterFunctionDefinition(self, ctx):
        """Track function definitions and analyze role management functions."""
        if not self.current_contract:
            return
            
        func_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.current_function = func_name
        
        # Check if this is a role management function
        is_role_function = self._is_role_management_function(func_name)
        
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
            'is_role_function': is_role_function,
            'has_auth_modifier': has_auth_modifier,
            'has_auth_require': has_auth_require,
            'visibility': self._get_function_visibility(ctx)
        }
        
        self.contract_functions[self.current_contract].append(function_info)
        
        if is_role_function:
            self.role_functions[self.current_contract].append(function_info)
    
    def enterExpressionStatement(self, ctx):
        """Check for authorization patterns in function bodies."""
        if not self.current_function or not self.current_contract:
            return
            
        expr_text = ctx.getText()
        
        # Check for authorization patterns
        for pattern in self.role_auth_patterns:
            if pattern in expr_text:
                # Mark current function as having auth require
                for func in self.contract_functions[self.current_contract]:
                    if func['name'] == self.current_function:
                        func['has_auth_require'] = True
                        break
                break
    
    def _is_role_management_function(self, func_name):
        """Check if function name suggests role management operations."""
        func_lower = func_name.lower()
        
        # Check for role management keywords
        return any(keyword in func_lower for keyword in self.role_keywords)
    
    def _get_function_visibility(self, ctx):
        """Get function visibility (public, external, internal, private)."""
        for child in ctx.children:
            if hasattr(child, 'getText'):
                text = child.getText()
                if text in ['public', 'external', 'internal', 'private']:
                    return text
        return 'public'  # Default visibility
    
    def _analyze_role_management(self):
        """Analyze role management functions for proper authorization."""
        if not self.current_contract:
            return
        
        role_funcs = self.role_functions[self.current_contract]
        role_vars = self.role_variables[self.current_contract]
        
        # Check each role management function for proper authorization
        for func in role_funcs:
            if not func['has_auth_modifier'] and not func['has_auth_require']:
                # Skip if function is internal or private (they have implicit access control)
                if func['visibility'] in ['internal', 'private']:
                    continue
                
                violation = {
                    'type': 'SCWE-017',
                    'contract': self.current_contract,
                    'function': func['name'],
                    'line': func['line'],
                    'message': f"Function '{func['name']}' allows unauthorized role assignment or privilege escalation"
                }
                self.violations.append(violation)
        
        # Check for role variables without proper initialization
        for role_var in role_vars:
            if role_var['name'].lower() in ['owner', 'admin', 'governor']:
                # Check if there's a constructor that initializes this role
                has_constructor_init = self._has_constructor_initialization(role_var['name'])
                if not has_constructor_init:
                    violation = {
                        'type': 'SCWE-017',
                        'contract': self.current_contract,
                        'function': 'N/A',
                        'line': role_var['line'],
                        'message': f"Role variable '{role_var['name']}' may not be properly initialized"
                    }
                    self.violations.append(violation)
    
    def _has_constructor_initialization(self, role_name):
        """Check if role variable is initialized in constructor."""
        # This is a simplified check - in practice, you'd analyze the constructor more carefully
        return True  # Simplified for this example
    
    def get_violations(self):
        """Return list of detected violations."""
        return self.violations
