from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class LackOfMultisigGovernanceDetector(SolidityParserListener):
    """
    Rule Code: 012
    Detects SCWE-012: Lack of Multisig Governance vulnerabilities
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.current_function = None
        self.processed_lines = set()  # Track processed lines to avoid duplicates
        
        # Track contract governance patterns
        self.contract_owners = {}  # contract_name -> [owner_variables]
        self.contract_functions = {}  # contract_name -> [function_info]
        self.contract_modifiers = {}  # contract_name -> [modifier_info]
        self.contract_inheritance = {}  # contract_name -> [parent_contracts]
        
        # Critical function patterns that should have multisig governance
        self.critical_functions = {
            'upgrade', 'upgradeTo', 'upgradeToAndCall', 'upgradeImplementation',
            'withdraw', 'withdrawFunds', 'withdrawAll', 'emergencyWithdraw',
            'pause', 'unpause', 'setPaused',
            'setOwner', 'transferOwnership', 'renounceOwnership',
            'setFee', 'setRate', 'setParameter', 'setConfig',
            'mint', 'burn', 'destroy', 'selfdestruct',
            'setImplementation', 'setProxy', 'setTarget'
        }
        
        # Multisig-related patterns (indicators of proper governance)
        self.multisig_patterns = {
            'multisig', 'gnosis', 'safe', 'timelock', 'governance', 'dao',
            'submitTransaction', 'confirmTransaction', 'executeTransaction',
            'requiredSignatures', 'signatureCount', 'isConfirmed',
            'multisigWallet', 'timelock', 'dao'
        }
        
    def enterContractDefinition(self, ctx):
        # Get contract name more robustly
        if ctx.identifier():
            self.current_contract = ctx.identifier().getText()
        else:
            self.current_contract = "UnknownContract"
            
        # Initialize contract data structures
        self.contract_owners[self.current_contract] = []
        self.contract_functions[self.current_contract] = []
        self.contract_modifiers[self.current_contract] = []
        self.contract_inheritance[self.current_contract] = []
        
        # Check inheritance for multisig contracts
        if ctx.inheritanceSpecifierList():
            for specifier in ctx.inheritanceSpecifierList().inheritanceSpecifier():
                parent_name = specifier.identifierPath().getText()
                self.contract_inheritance[self.current_contract].append(parent_name)
        
    def exitContractDefinition(self, ctx):
        # Analyze governance patterns for this contract
        self._analyze_governance_patterns()
        self.current_contract = None
        
    def enterFunctionDefinition(self, ctx):
        # Get function name more robustly
        if ctx.identifier():
            self.current_function = ctx.identifier().getText()
        else:
            self.current_function = "unknown"
        
        # Only process if we have a valid contract context
        if not self.current_contract:
            return
            
        # Collect function information
        function_info = {
            'name': self.current_function,
            'line': ctx.start.line,
            'modifiers': [],
            'has_owner_check': False,
            'has_multisig_check': False,
            'is_critical': False
        }
        
        # Check if function name suggests critical operations
        function_lower = self.current_function.lower()
        for critical_pattern in self.critical_functions:
            if critical_pattern in function_lower:
                function_info['is_critical'] = True
                break
        
        # Collect modifiers
        if ctx.modifierInvocation():
            for modifier in ctx.modifierInvocation():
                modifier_name = modifier.identifierPath().getText()
                function_info['modifiers'].append(modifier_name)
                
                # Check for multisig-related modifiers
                modifier_lower = modifier_name.lower()
                for multisig_pattern in self.multisig_patterns:
                    if multisig_pattern in modifier_lower:
                        function_info['has_multisig_check'] = True
                        break
        
        self.contract_functions[self.current_contract].append(function_info)
        
    def exitFunctionDefinition(self, ctx):
        self.current_function = None
        
    def enterStateVariableDeclaration(self, ctx):
        if not self.current_contract:
            return
            
        var_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        var_line = ctx.start.line
        
        # Check for owner-related variables
        var_lower = var_name.lower()
        if 'owner' in var_lower or 'admin' in var_lower or 'governor' in var_lower:
            self.contract_owners[self.current_contract].append({
                'name': var_name,
                'line': var_line
            })
            
    def enterExpressionStatement(self, ctx):
        """Check for owner validation patterns in function bodies"""
        if not self.current_function or not self.current_contract:
            return
            
        expr_text = ctx.getText()
        line = ctx.start.line
        
        # Check for owner validation patterns
        if 'require(' in expr_text and 'msg.sender' in expr_text:
            # Check if it's a single owner check (insecure) or multisig check (secure)
            is_multisig = False
            is_owner_check = False
            
            # Check for multisig patterns first
            for multisig_pattern in self.multisig_patterns:
                if multisig_pattern in expr_text.lower():
                    is_multisig = True
                    break
            
            # Check for single owner patterns
            if 'owner' in expr_text.lower() or 'admin' in expr_text.lower():
                is_owner_check = True
            
            # Update function info
            for func_info in self.contract_functions[self.current_contract]:
                if func_info['name'] == self.current_function:
                    if is_multisig:
                        func_info['has_multisig_check'] = True
                    elif is_owner_check:
                        func_info['has_owner_check'] = True
                    break
                        
    def _analyze_governance_patterns(self):
        """Analyze the contract for governance patterns"""
        if not self.current_contract:
            return
            
        contract_name = self.current_contract
        owners = self.contract_owners.get(contract_name, [])
        functions = self.contract_functions.get(contract_name, [])
        inheritance = self.contract_inheritance.get(contract_name, [])
        
        # Check if contract inherits from multisig contracts
        has_multisig_inheritance = False
        for parent in inheritance:
            parent_lower = parent.lower()
            for multisig_pattern in self.multisig_patterns:
                if multisig_pattern in parent_lower:
                    has_multisig_inheritance = True
                    break
            if has_multisig_inheritance:
                break
        
        # Check for critical functions without proper governance
        for func_info in functions:
            if func_info['is_critical']:
                # Check if this critical function has proper governance
                has_proper_governance = (
                    func_info['has_multisig_check'] or 
                    has_multisig_inheritance or
                    self._has_multisig_variables(contract_name)
                )
                
                if not has_proper_governance:
                    # Check if it has basic owner check (single point of failure)
                    if func_info['has_owner_check']:
                        self.violations.append(
                            f"SCWE-012: Lack of multisig governance detected in contract '{contract_name}': "
                            f"Critical function '{func_info['name']}' at line {func_info['line']} uses single-owner "
                            f"access control. Implement multisig governance for enhanced security."
                        )
                    else:
                        # No access control at all
                        self.violations.append(
                            f"SCWE-012: Critical function without access control detected in contract '{contract_name}': "
                            f"Function '{func_info['name']}' at line {func_info['line']} has no access control. "
                            f"Implement multisig governance for critical operations."
                        )
        
        # Check for single owner pattern (centralization risk)
        if len(owners) == 1 and not has_multisig_inheritance:
            owner_var = owners[0]
            self.violations.append(
                f"SCWE-012: Centralized governance detected in contract '{contract_name}': "
                f"Single owner variable '{owner_var['name']}' at line {owner_var['line']} creates "
                f"centralization risk. Consider implementing multisig governance."
            )
            
    def _has_multisig_variables(self, contract_name):
        """Check if contract has multisig-related variables"""
        # This would require more sophisticated analysis of variable names and types
        # For now, we'll rely on inheritance and modifier patterns
        return False

    def get_violations(self):
        return self.violations
