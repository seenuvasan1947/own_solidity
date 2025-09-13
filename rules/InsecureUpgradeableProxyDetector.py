from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class InsecureUpgradeableProxyDetector(SolidityParserListener):
    """
    Rule Code: 005
    Detects SCWE-005: Insecure Upgradeable Proxy Design vulnerabilities
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None
        self.function_visibility = None
        self.function_modifiers = []
        self.found_access_control = False
        self.found_timelock = False
        self.proxy_functions = []
        self.implementation_variables = []
        
    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.proxy_functions = []
        self.implementation_variables = []
        
    def exitContractDefinition(self, ctx):
        # Check if this contract has proxy-like functionality
        if self.implementation_variables and self.proxy_functions:
            self._check_proxy_security()
        self.current_contract = None
        
    def enterStateVariableDeclaration(self, ctx):
        if not self.current_contract:
            return
            
        var_name = ctx.identifier().getText() if ctx.identifier() else ""
        var_text = ctx.getText().lower()
        
        # Check for implementation-related variables
        if any(keyword in var_text for keyword in ['implementation', 'logic', 'target', 'beacon']):
            self.implementation_variables.append(var_name)
            
    def enterFunctionDefinition(self, ctx):
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.function_visibility = self._get_function_visibility(ctx)
        self.function_modifiers = self._get_function_modifiers(ctx)
        self.found_access_control = False
        self.found_timelock = False
        
    def exitFunctionDefinition(self, ctx):
        if not self.in_function:
            return
            
        # Check if this function modifies implementation
        func_text = ctx.getText().lower()
        if any(keyword in func_text for keyword in ['implementation', 'setimplementation', 'upgrade', 'update']):
            self.proxy_functions.append({
                'name': self.function_name,
                'visibility': self.function_visibility,
                'modifiers': self.function_modifiers,
                'has_access_control': self.found_access_control,
                'has_timelock': self.found_timelock,
                'line': ctx.start.line
            })
            
        self.in_function = False
        self.function_name = None
        self.function_visibility = None
        self.function_modifiers = []
        self.found_access_control = False
        self.found_timelock = False
        
    def enterModifierInvocation(self, ctx):
        if not self.in_function:
            return
            
        modifier_text = ctx.getText().lower()
        
        # Check for access control modifiers
        access_control_modifiers = [
            'onlyowner', 'onlyadmin', 'onlyauthorized', 'onlyrole',
            'hasrole', 'requireowner', 'requireadmin', 'auth', 'authorized'
        ]
        
        if any(pattern in modifier_text for pattern in access_control_modifiers):
            self.found_access_control = True
            
        # Check for timelock modifiers
        timelock_modifiers = [
            'timelock', 'delay', 'upgradeable', 'scheduled'
        ]
        
        if any(pattern in modifier_text for pattern in timelock_modifiers):
            self.found_timelock = True
            
    def enterExpressionStatement(self, ctx):
        if not self.in_function:
            return

        expr_text = ctx.getText().lower()

        # Look for access control patterns
        access_patterns = [
            'msg.sender', 'require(msg.sender', 'msg.sender ==',
            'onlyowner', 'onlyadmin', 'hasrole('
        ]

        if any(pattern in expr_text for pattern in access_patterns):
            self.found_access_control = True
            
        # Look for timelock patterns
        timelock_patterns = [
            'block.timestamp', 'now', 'timelock', 'delay', 'upgrade'
        ]
        
        if any(pattern in expr_text for pattern in timelock_patterns):
            self.found_timelock = True
            
    def _check_proxy_security(self):
        """Check if proxy functions have proper security measures"""
        for func in self.proxy_functions:
            issues = []
            
            # Check for missing access control
            if not func['has_access_control']:
                issues.append("missing access control")
                
            # Check for missing timelock
            if not func['has_timelock']:
                issues.append("missing timelock mechanism")
                
            # Check for public/external visibility without proper controls
            if func['visibility'] in ['public', 'external'] and not func['has_access_control']:
                issues.append("public/external function without access control")
                
            if issues:
                self.violations.append(
                    f"SCWE-005: Insecure upgradeable proxy design in function '{func['name']}' "
                    f"of contract '{self.current_contract}' at line {func['line']}: "
                    f"{', '.join(issues)}"
                )
                
    def _get_function_visibility(self, ctx):
        """Extract function visibility"""
        try:
            i = 0
            while True:
                vis = ctx.visibility(i)
                if vis is None:
                    break
                vis_text = vis.getText()
                if vis_text in ['public', 'external', 'internal', 'private']:
                    return vis_text
                i += 1
            return "public"  # Default visibility
        except Exception:
            return "public"
            
    def _get_function_modifiers(self, ctx):
        """Extract function modifiers"""
        modifiers = []
        try:
            i = 0
            while True:
                mod = ctx.modifierList(i)
                if mod is None:
                    break
                modifier_text = mod.getText()
                modifiers.append(modifier_text)
                i += 1
        except Exception:
            pass
        return modifiers

    def get_violations(self):
        return self.violations
