from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class UnauthorizedParameterChangesDetector(SolidityParserListener):
    """
    Detector for SCWE-013: Unauthorized Parameter Changes
    Rule Code: 013
    
    Detects functions that modify critical parameters without proper access control,
    multisig governance, or timelock mechanisms.
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.current_function = None
        self.contract_functions = {}  # contract_name -> list of function info
        self.state_variables = {}  # contract_name -> list of state variables
        self.parameter_modification_functions = {}  # contract_name -> list of functions that modify parameters
        
        # Keywords that indicate parameter modification functions
        self.parameter_keywords = [
            'set', 'update', 'change', 'modify', 'configure', 'adjust',
            'fee', 'rate', 'limit', 'threshold', 'cap', 'max', 'min',
            'price', 'cost', 'amount', 'value', 'config', 'setting'
        ]
        
        # Access control patterns
        self.access_control_patterns = [
            'onlyOwner', 'onlyAdmin', 'onlyGovernance', 'onlyRole', 'onlyMultisig',
            'require(msg.sender == owner)', 'require(msg.sender == admin)',
            'require(msg.sender == multisigWallet)', 'require(msg.sender == governance)',
            'require(hasRole(', 'require(isOwner(', 'require(isAdmin(',
            'require(admins[msg.sender]'
        ]
        
        # Governance patterns (multisig, timelock, DAO)
        self.governance_patterns = [
            'multisig', 'timelock', 'governance', 'dao', 'voting',
            'proposal', 'approve', 'execute', 'queue', 'delay',
            'queuedTransactions', 'TIMELOCK_DELAY', 'queueParameterChange',
            'executeParameterChange'
        ]
        
        # Critical parameter patterns
        self.critical_parameters = [
            'fee', 'rate', 'price', 'cost', 'amount', 'limit', 'threshold',
            'cap', 'max', 'min', 'config', 'setting', 'parameter', 'value'
        ]
    
    def enterContractDefinition(self, ctx):
        """Track contract definitions and initialize data structures."""
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "UnknownContract"
        self.contract_functions[self.current_contract] = []
        self.state_variables[self.current_contract] = []
        self.parameter_modification_functions[self.current_contract] = []
    
    def exitContractDefinition(self, ctx):
        """Analyze parameter modification functions after processing the contract."""
        if self.current_contract:
            self._analyze_parameter_changes()
        self.current_contract = None
    
    def enterStateVariableDeclaration(self, ctx):
        """Track state variables that might be critical parameters."""
        if not self.current_contract:
            return
            
        var_name = ctx.identifier().getText() if ctx.identifier() else ""
        var_type = ctx.typeName().getText() if ctx.typeName() else ""
        
        # Check if this is a critical parameter
        is_critical = any(keyword in var_name.lower() for keyword in self.critical_parameters)
        
        self.state_variables[self.current_contract].append({
            'name': var_name,
            'type': var_type,
            'is_critical': is_critical,
            'line': ctx.start.line
        })
    
    def enterFunctionDefinition(self, ctx):
        """Track function definitions and analyze parameter modification functions."""
        if not self.current_contract:
            return
            
        func_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.current_function = func_name
        
        # Check if this function modifies parameters
        is_parameter_function = self._is_parameter_modification_function(func_name)
        
        # Collect modifiers and check for access control
        modifiers = []
        has_access_control = False
        for child in ctx.children:
            if hasattr(child, 'getText'):
                modifier_text = child.getText()
                if modifier_text in ['onlyOwner', 'onlyAdmin', 'onlyGovernance', 'onlyRole', 'onlyMultisig']:
                    modifiers.append(modifier_text)
                    has_access_control = True
        
        function_info = {
            'name': func_name,
            'line': ctx.start.line,
            'is_parameter_function': is_parameter_function,
            'modifiers': modifiers,
            'has_access_control': has_access_control,
            'has_governance': False,
            'modifies_critical_params': False
        }
        
        self.contract_functions[self.current_contract].append(function_info)
        
        if is_parameter_function:
            self.parameter_modification_functions[self.current_contract].append(function_info)
    
    def enterExpressionStatement(self, ctx):
        """Check for access control patterns in function bodies."""
        if not self.current_function or not self.current_contract:
            return
            
        expr_text = ctx.getText()
        
        # Check for access control patterns
        for pattern in self.access_control_patterns:
            if pattern in expr_text:
                self._mark_function_has_access_control()
                break
        
        # Check for governance patterns
        for pattern in self.governance_patterns:
            if pattern in expr_text.lower():
                self._mark_function_has_governance()
                break
        
        # Check if this modifies critical parameters
        if self._modifies_critical_parameter(expr_text):
            self._mark_function_modifies_critical_params()
    
    def enterAssignment(self, ctx):
        """Check for assignments to critical parameters."""
        if not self.current_function or not self.current_contract:
            return
            
        # Get the left side of the assignment (variable being assigned)
        left_expr = ctx.expression(0)
        if left_expr:
            var_name = left_expr.getText()
            
            # Check if this is a critical parameter
            if any(keyword in var_name.lower() for keyword in self.critical_parameters):
                self._mark_function_modifies_critical_params()
    
    def _is_parameter_modification_function(self, func_name):
        """Check if function name suggests parameter modification."""
        func_lower = func_name.lower()
        return any(keyword in func_lower for keyword in self.parameter_keywords)
    
    def _modifies_critical_parameter(self, expr_text):
        """Check if expression modifies critical parameters."""
        expr_lower = expr_text.lower()
        return any(keyword in expr_lower for keyword in self.critical_parameters)
    
    def _mark_function_has_access_control(self):
        """Mark current function as having access control."""
        if self.current_contract and self.current_function:
            for func in self.contract_functions[self.current_contract]:
                if func['name'] == self.current_function:
                    func['has_access_control'] = True
                    break
    
    def _mark_function_has_governance(self):
        """Mark current function as having governance mechanisms."""
        if self.current_contract and self.current_function:
            for func in self.contract_functions[self.current_contract]:
                if func['name'] == self.current_function:
                    func['has_governance'] = True
                    break
    
    def _mark_function_modifies_critical_params(self):
        """Mark current function as modifying critical parameters."""
        if self.current_contract and self.current_function:
            for func in self.contract_functions[self.current_contract]:
                if func['name'] == self.current_function:
                    func['modifies_critical_params'] = True
                    break
    
    def _analyze_parameter_changes(self):
        """Analyze parameter modification functions for unauthorized changes."""
        if not self.current_contract:
            return
            
        for func in self.parameter_modification_functions[self.current_contract]:
            # Check if function modifies critical parameters without proper controls
            if (func['modifies_critical_params'] and 
                not func['has_access_control'] and 
                not func['has_governance']):
                
                violation = {
                    'type': 'SCWE-013',
                    'contract': self.current_contract,
                    'function': func['name'],
                    'line': func['line'],
                    'message': f"Function '{func['name']}' modifies critical parameters without proper access control or governance mechanisms"
                }
                self.violations.append(violation)
    
    def get_violations(self):
        """Return list of detected violations."""
        return self.violations
