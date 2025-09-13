from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class UnusedVariablesDetector(SolidityParserListener):
    """
    Rule Code: 007
    Detects SCWE-007: Presence of Unused Variables vulnerabilities
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.current_function = None
        self.declared_variables = {}  # contract_name -> [variables]
        self.used_variables = set()   # Set of all used variable names
        self.function_variables = {}  # function_name -> [variables]
        self.function_used_vars = set()  # Set of variables used in current function
        self.declaring_variable = False  # Flag to track when we're declaring a variable
        
    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.declared_variables[self.current_contract] = []
        
    def exitContractDefinition(self, ctx):
        # Check for unused state variables in this contract
        self._check_unused_state_variables()
        self.current_contract = None
        
    def enterFunctionDefinition(self, ctx):
        self.current_function = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.function_variables[self.current_function] = []
        self.function_used_vars = set()
        
    def exitFunctionDefinition(self, ctx):
        # Check for unused local variables in this function
        self._check_unused_function_variables()
        self.current_function = None
        self.function_used_vars = set()
        
    def enterStateVariableDeclaration(self, ctx):
        if not self.current_contract:
            return
            
        self.declaring_variable = True
        var_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        var_line = ctx.start.line
        
        # Skip public variables as they are automatically getters
        visibility = self._get_variable_visibility(ctx)
        is_public = visibility == 'public'
        
        
        self.declared_variables[self.current_contract].append({
            'name': var_name,
            'line': var_line,
            'is_public': is_public,
            'visibility': visibility
        })
        
    def exitStateVariableDeclaration(self, ctx):
        self.declaring_variable = False
        
    def enterVariableDeclarationStatement(self, ctx):
        if not self.current_function:
            return
            
        self.declaring_variable = True
        
        # Handle single variable declaration
        if ctx.variableDeclaration():
            var_decl = ctx.variableDeclaration()
            var_name = var_decl.identifier().getText() if var_decl.identifier() else "unknown"
            var_line = ctx.start.line
            
            
            self.function_variables[self.current_function].append({
                'name': var_name,
                'line': var_line
            })
        
        # Handle tuple variable declaration
        elif ctx.variableDeclarationTuple():
            tuple_decl = ctx.variableDeclarationTuple()
            for var_decl in tuple_decl.variableDeclarations:
                var_name = var_decl.identifier().getText() if var_decl.identifier() else "unknown"
                var_line = ctx.start.line
                
                print(f"Tuple variable: {var_name} in {self.current_function}")
                
                self.function_variables[self.current_function].append({
                    'name': var_name,
                    'line': var_line
                })
                
    def exitVariableDeclarationStatement(self, ctx):
        self.declaring_variable = False
                
    def enterIdentifier(self, ctx):
        var_name = ctx.getText()
        
        # Don't count variable declarations as usage
        if not self.declaring_variable:
            # Track variable usage
            print(f"Using identifier: {var_name}")
            self.used_variables.add(var_name)
            if self.current_function:
                self.function_used_vars.add(var_name)
            
    def enterMemberAccess(self, ctx):
        # Handle member access like contract.variable
        if ctx.identifier():
            var_name = ctx.identifier().getText()
            self.used_variables.add(var_name)
            if self.current_function:
                self.function_used_vars.add(var_name)
                
    def _check_unused_state_variables(self):
        """Check for unused state variables in the current contract"""
        if not self.current_contract:
            return
            
        contract_vars = self.declared_variables.get(self.current_contract, [])
        
        for var in contract_vars:
            var_name = var['name']
            
            # Skip public variables as they have automatic getters
            if var['is_public']:
                continue
                
            # Check if variable is used anywhere in the contract
            if var_name not in self.used_variables:
                self.violations.append(
                    f"SCWE-007: Unused state variable '{var_name}' in contract '{self.current_contract}' "
                    f"at line {var['line']}: Variable is declared but never used."
                )
                
    def _check_unused_function_variables(self):
        """Check for unused local variables in the current function"""
        if not self.current_function:
            return
            
        func_vars = self.function_variables.get(self.current_function, [])
        
        for var in func_vars:
            var_name = var['name']
            
            # Check if variable is used in this function
            if var_name not in self.function_used_vars:
                self.violations.append(
                    f"SCWE-007: Unused local variable '{var_name}' in function '{self.current_function}' "
                    f"of contract '{self.current_contract}' at line {var['line']}: Variable is declared but never used."
                )
                
    def _get_variable_visibility(self, ctx):
        """Extract variable visibility from state variable declaration"""
        try:
            # Check for visibility modifiers in the state variable declaration
            # The grammar shows: type = typeName (Public | Private | Internal | Constant | overrideSpecifier | Immutable | Transient)* name = identifier
            for i in range(ctx.getChildCount()):
                child = ctx.getChild(i)
                if hasattr(child, 'getText'):
                    child_text = child.getText()
                    if child_text in ['public', 'private', 'internal']:
                        return child_text
            return 'internal'  # Default visibility for state variables
        except Exception:
            return 'internal'

    def get_violations(self):
        return self.violations
