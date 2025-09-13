from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class ShadowingDetector(SolidityParserListener):
    """
    Rule Code: 010
    Detects SCWE-010: Shadowing Variables and Functions vulnerabilities
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.current_function = None
        self.contract_variables = {}  # contract_name -> [variable_names]
        self.contract_functions = {}  # contract_name -> [function_names]
        self.function_parameters = {}  # function_name -> [parameter_names]
        self.function_local_vars = {}  # function_name -> [local_var_names]
        self.scope_stack = []  # Stack to track nested scopes
        
    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.contract_variables[self.current_contract] = []
        self.contract_functions[self.current_contract] = []
        
    def exitContractDefinition(self, ctx):
        self.current_contract = None
        
    def enterFunctionDefinition(self, ctx):
        self.current_function = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.function_parameters[self.current_function] = []
        self.function_local_vars[self.current_function] = []
        
        # Add function name to contract functions
        if self.current_contract:
            self.contract_functions[self.current_contract].append(self.current_function)
            
    def exitFunctionDefinition(self, ctx):
        # Check for shadowing issues in this function
        self._check_function_shadowing()
        self.current_function = None
        
    def enterStateVariableDeclaration(self, ctx):
        if not self.current_contract:
            return
            
        var_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        var_line = ctx.start.line
        
        # Check if this variable shadows a function
        if self.current_contract in self.contract_functions:
            if var_name in self.contract_functions[self.current_contract]:
                self.violations.append(
                    f"SCWE-010: Variable shadowing detected in contract '{self.current_contract}': "
                    f"State variable '{var_name}' at line {var_line} shadows function with the same name."
                )
        
        # Add to contract variables
        self.contract_variables[self.current_contract].append(var_name)
        
    def enterParameterDeclaration(self, ctx):
        if not self.current_function:
            return
            
        param_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        param_line = ctx.start.line
        
        # Check if parameter shadows contract variable
        if self.current_contract and self.current_contract in self.contract_variables:
            if param_name in self.contract_variables[self.current_contract]:
                self.violations.append(
                    f"SCWE-010: Parameter shadowing detected in function '{self.current_function}' "
                    f"of contract '{self.current_contract}': Parameter '{param_name}' at line {param_line} "
                    f"shadows state variable with the same name."
                )
        
        # Check if parameter shadows function name
        if self.current_contract and self.current_contract in self.contract_functions:
            if param_name in self.contract_functions[self.current_contract]:
                self.violations.append(
                    f"SCWE-010: Parameter shadowing detected in function '{self.current_function}' "
                    f"of contract '{self.current_contract}': Parameter '{param_name}' at line {param_line} "
                    f"shadows function with the same name."
                )
        
        # Add to function parameters
        self.function_parameters[self.current_function].append(param_name)
        
    def enterVariableDeclarationStatement(self, ctx):
        if not self.current_function:
            return
            
        # Handle single variable declaration
        if ctx.variableDeclaration():
            var_decl = ctx.variableDeclaration()
            var_name = var_decl.identifier().getText() if var_decl.identifier() else "unknown"
            var_line = ctx.start.line
            
            self._check_local_variable_shadowing(var_name, var_line)
            self.function_local_vars[self.current_function].append(var_name)
        
        # Handle tuple variable declaration
        elif ctx.variableDeclarationTuple():
            tuple_decl = ctx.variableDeclarationTuple()
            for var_decl in tuple_decl.variableDeclarations:
                var_name = var_decl.identifier().getText() if var_decl.identifier() else "unknown"
                var_line = ctx.start.line
                
                self._check_local_variable_shadowing(var_name, var_line)
                self.function_local_vars[self.current_function].append(var_name)
                
    def _check_local_variable_shadowing(self, var_name, var_line):
        """Check if local variable shadows outer scope variables"""
        # Check if local variable shadows contract variable
        if self.current_contract and self.current_contract in self.contract_variables:
            if var_name in self.contract_variables[self.current_contract]:
                self.violations.append(
                    f"SCWE-010: Local variable shadowing detected in function '{self.current_function}' "
                    f"of contract '{self.current_contract}': Local variable '{var_name}' at line {var_line} "
                    f"shadows state variable with the same name."
                )
        
        # Check if local variable shadows function parameter
        if self.current_function and self.current_function in self.function_parameters:
            if var_name in self.function_parameters[self.current_function]:
                self.violations.append(
                    f"SCWE-010: Local variable shadowing detected in function '{self.current_function}' "
                    f"of contract '{self.current_contract}': Local variable '{var_name}' at line {var_line} "
                    f"shadows function parameter with the same name."
                )
        
        # Check if local variable shadows function name
        if self.current_contract and self.current_contract in self.contract_functions:
            if var_name in self.contract_functions[self.current_contract]:
                self.violations.append(
                    f"SCWE-010: Local variable shadowing detected in function '{self.current_function}' "
                    f"of contract '{self.current_contract}': Local variable '{var_name}' at line {var_line} "
                    f"shadows function with the same name."
                )
                
    def _check_function_shadowing(self):
        """Check for function shadowing within the current function"""
        if not self.current_function or not self.current_contract:
            return
            
        # Check if function name shadows contract variable
        if self.current_contract in self.contract_variables:
            if self.current_function in self.contract_variables[self.current_contract]:
                self.violations.append(
                    f"SCWE-010: Function shadowing detected in contract '{self.current_contract}': "
                    f"Function '{self.current_function}' shadows state variable with the same name."
                )

    def get_violations(self):
        return self.violations
