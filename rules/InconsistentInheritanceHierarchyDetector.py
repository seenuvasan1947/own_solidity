from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class InconsistentInheritanceHierarchyDetector(SolidityParserListener):
    """
    Rule Code: 006
    Detects SCWE-006: Inconsistent Inheritance Hierarchy vulnerabilities
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.contract_inheritance = {}
        self.contract_functions = {}
        self.contract_variables = {}
        self.inheritance_chain = []
        
    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.contract_inheritance[self.current_contract] = []
        self.contract_functions[self.current_contract] = []
        self.contract_variables[self.current_contract] = []
        
        # Extract inheritance list
        inheritance_list = ctx.inheritanceSpecifierList()
        if inheritance_list:
            for i in range(inheritance_list.getChildCount()):
                child = inheritance_list.getChild(i)
                # Check if this is an InheritanceSpecifierContext
                if hasattr(child, 'identifierPath') and child.identifierPath():
                    parent_name = child.identifierPath().getText()
                    self.contract_inheritance[self.current_contract].append(parent_name)
                elif hasattr(child, 'identifier') and child.identifier():
                    parent_name = child.identifier().getText()
                    self.contract_inheritance[self.current_contract].append(parent_name)
                # Skip terminal nodes like 'is', ','
                elif hasattr(child, 'getText') and child.getText() not in ['is', ',']:
                    # This might be a direct identifier
                    child_text = child.getText()
                    if child_text and child_text not in ['is', ',']:
                        self.contract_inheritance[self.current_contract].append(child_text)
        
                    
    def exitContractDefinition(self, ctx):
        # Check for inheritance issues after processing the contract
        self._check_inheritance_consistency()
        self.current_contract = None
        
    def enterFunctionDefinition(self, ctx):
        if not self.current_contract:
            return
            
        func_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        func_signature = self._get_function_signature(ctx)
        
        self.contract_functions[self.current_contract].append({
            'name': func_name,
            'signature': func_signature,
            'line': ctx.start.line
        })
        
        
    def enterStateVariableDeclaration(self, ctx):
        if not self.current_contract:
            return
            
        var_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        var_type = self._get_variable_type(ctx)
        
        self.contract_variables[self.current_contract].append({
            'name': var_name,
            'type': var_type,
            'line': ctx.start.line
        })
        
    def _check_inheritance_consistency(self):
        """Check for inconsistent inheritance patterns"""
        if not self.current_contract:
            return
            
        contract_name = self.current_contract
        parents = self.contract_inheritance.get(contract_name, [])
        
        
        # Check for diamond problem (multiple inheritance with conflicting functions)
        if len(parents) > 1:
            self._check_diamond_problem(contract_name, parents)
            
        # Check for ambiguous function overrides
        self._check_ambiguous_overrides(contract_name, parents)
        
        # Check for conflicting variable definitions
        self._check_conflicting_variables(contract_name, parents)
        
    def _check_diamond_problem(self, contract_name, parents):
        """Check for diamond problem in multiple inheritance"""
        all_parent_functions = {}
        conflicting_functions = []
        
        # Collect all functions from parent contracts
        for parent in parents:
            if parent in self.contract_functions:
                for func in self.contract_functions[parent]:
                    func_key = func['signature']
                    if func_key in all_parent_functions:
                        # Function exists in multiple parents
                        if all_parent_functions[func_key] != parent:
                            conflicting_functions.append({
                                'function': func['name'],
                                'signature': func_key,
                                'parents': [all_parent_functions[func_key], parent]
                            })
                    else:
                        all_parent_functions[func_key] = parent
        
        # Report diamond problem issues
        for conflict in conflicting_functions:
            self.violations.append(
                f"SCWE-006: Diamond problem detected in contract '{contract_name}': "
                f"Function '{conflict['function']}' is defined in multiple parent contracts "
                f"({', '.join(conflict['parents'])}). This can lead to ambiguous behavior."
            )
            
    def _check_ambiguous_overrides(self, contract_name, parents):
        """Check for ambiguous function overrides"""
        contract_functions = self.contract_functions.get(contract_name, [])
        
        for func in contract_functions:
            func_name = func['name']
            func_signature = func['signature']
            
            # Check if this function exists in multiple parents
            parent_implementations = []
            for parent in parents:
                if parent in self.contract_functions:
                    for parent_func in self.contract_functions[parent]:
                        if parent_func['signature'] == func_signature:
                            if parent not in parent_implementations:  # Avoid duplicates
                                parent_implementations.append(parent)
                            
            if len(parent_implementations) > 1:
                # For now, we'll skip the explicit parent call check since we don't have the function text
                # This is a simplified version that flags any function existing in multiple parents
                self.violations.append(
                    f"SCWE-006: Ambiguous function override in contract '{contract_name}': "
                    f"Function '{func_name}' at line {func['line']} exists in multiple parent contracts "
                    f"({', '.join(parent_implementations)}) but doesn't explicitly specify which parent to call."
                )
                    
    def _check_conflicting_variables(self, contract_name, parents):
        """Check for conflicting variable definitions"""
        contract_variables = self.contract_variables.get(contract_name, [])
        
        for var in contract_variables:
            var_name = var['name']
            var_type = var['type']
            
            # Check if this variable exists in parent contracts
            conflicting_parents = []
            for parent in parents:
                if parent in self.contract_variables:
                    for parent_var in self.contract_variables[parent]:
                        if parent_var['name'] == var_name and parent_var['type'] != var_type:
                            conflicting_parents.append(parent)
                            
            if conflicting_parents:
                self.violations.append(
                    f"SCWE-006: Conflicting variable definition in contract '{contract_name}': "
                    f"Variable '{var_name}' at line {var['line']} has conflicting type definitions "
                    f"with parent contracts ({', '.join(conflicting_parents)})."
                )
                
    def _get_function_signature(self, ctx):
        """Extract function signature for comparison"""
        try:
            func_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
            params = ctx.parameterList()
            param_text = params.getText() if params else "()"
            return f"{func_name}{param_text}"
        except Exception:
            return "unknown"
            
    def _get_variable_type(self, ctx):
        """Extract variable type"""
        try:
            type_name = ctx.typeName()
            if type_name:
                return type_name.getText()
            return "unknown"
        except Exception:
            return "unknown"
            
    def _get_function_text(self, func):
        """Get function text for analysis (simplified)"""
        # This is a simplified version - in a real implementation,
        # you'd need to store the actual function text during parsing
        return ""

    def get_violations(self):
        return self.violations
