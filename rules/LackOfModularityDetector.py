from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class LackOfModularityDetector(SolidityParserListener):
    """
    Rule Code: 003
    Detects lack of modularity as defined in SCWE-003
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.contract_functions = []
        self.contract_state_variables = []
        self.contract_imports = []
        self.contract_uses_libraries = False
        self.contract_inheritance_count = 0
        self.function_responsibilities = []
        self.current_function = None
        self.function_state_access_count = 0
        self.function_external_calls = 0
        
    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.contract_functions = []
        self.contract_state_variables = []
        self.contract_imports = []
        self.contract_uses_libraries = False
        self.contract_inheritance_count = 0
        self.function_responsibilities = []
        
    def exitContractDefinition(self, ctx):
        # Check contract-level modularity issues
        self._check_contract_modularity()
        self.current_contract = None
        
    def enterImportDirective(self, ctx):
        if self.current_contract:
            import_path = ctx.path().getText() if ctx.path() else ""
            self.contract_imports.append(import_path)
    
    def enterInheritanceSpecifierList(self, ctx):
        if self.current_contract:
            self.contract_inheritance_count = len(ctx.inheritanceSpecifier())
    
    def enterStateVariableDeclaration(self, ctx):
        if self.current_contract:
            var_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
            var_type = ctx.typeName().getText() if ctx.typeName() else "unknown"
            self.contract_state_variables.append({
                'name': var_name,
                'type': var_type
            })
    
    def enterFunctionDefinition(self, ctx):
        self.current_function = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.function_state_access_count = 0
        self.function_external_calls = 0
        self.function_responsibilities = []
        
    def exitFunctionDefinition(self, ctx):
        if self.current_function:
            # Analyze function responsibilities
            self._analyze_function_responsibilities()
        self.current_function = None
    
    def enterUsingDirective(self, ctx):
        if self.current_contract:
            self.contract_uses_libraries = True
    
    def enterMemberAccess(self, ctx):
        if self.current_function:
            # Check if accessing state variables
            member_text = ctx.getText()
            if any(var['name'] in member_text for var in self.contract_state_variables):
                self.function_state_access_count += 1
    
    def enterFunctionCall(self, ctx):
        if self.current_function:
            # Check for external calls
            call_text = ctx.getText()
            external_call_patterns = [
                'transfer(',
                'call(',
                'delegatecall(',
                'staticcall(',
                'send(',
                'approve(',
                'transferFrom('
            ]
            if any(pattern in call_text for pattern in external_call_patterns):
                self.function_external_calls += 1
    
    def _analyze_function_responsibilities(self):
        """Analyze what responsibilities a function has"""
        if not self.current_function:
            return
            
        responsibilities = []
        
        # Check for different types of responsibilities
        if self.function_state_access_count > 0:
            responsibilities.append("state_management")
        
        if self.function_external_calls > 0:
            responsibilities.append("external_interaction")
        
        # Check function name patterns for responsibilities
        func_name_lower = self.current_function.lower()
        if any(keyword in func_name_lower for keyword in ['transfer', 'send', 'withdraw', 'deposit']):
            responsibilities.append("token_operations")
        if any(keyword in func_name_lower for keyword in ['approve', 'allowance']):
            responsibilities.append("approval_management")
        if any(keyword in func_name_lower for keyword in ['mint', 'burn']):
            responsibilities.append("supply_management")
        if any(keyword in func_name_lower for keyword in ['pause', 'unpause', 'emergency']):
            responsibilities.append("access_control")
        if any(keyword in func_name_lower for keyword in ['update', 'set', 'change']):
            responsibilities.append("configuration")
        
        self.function_responsibilities = responsibilities
    
    def _check_contract_modularity(self):
        """Check for lack of modularity issues"""
        if not self.current_contract:
            return
        
        # Rule 1: Monolithic contract - too many responsibilities in one contract
        unique_responsibilities = set()
        for func in self.contract_functions:
            if hasattr(func, 'responsibilities'):
                unique_responsibilities.update(func.responsibilities)
        
        if len(unique_responsibilities) > 4:
            self.violations.append(
                f"❌ Lack of modularity in '{self.current_contract}': "
                f"Contract handles {len(unique_responsibilities)} different responsibilities. "
                f"Consider splitting into separate contracts or using libraries."
            )
        
        # Rule 2: No library usage - contract doesn't use any libraries
        if not self.contract_uses_libraries and len(self.contract_functions) > 5:
            self.violations.append(
                f"❌ Lack of modularity in '{self.current_contract}': "
                f"Contract has {len(self.contract_functions)} functions but doesn't use any libraries. "
                f"Consider using libraries for reusable functionality."
            )
        
        # Rule 3: Too many state variables - indicates tight coupling
        if len(self.contract_state_variables) > 10:
            self.violations.append(
                f"❌ Lack of modularity in '{self.current_contract}': "
                f"Contract has {len(self.contract_state_variables)} state variables. "
                f"Consider grouping related variables into structs or separate contracts."
            )
        
        # Rule 4: No inheritance - contract doesn't inherit from any base contracts
        if self.contract_inheritance_count == 0 and len(self.contract_functions) > 8:
            self.violations.append(
                f"❌ Lack of modularity in '{self.current_contract}': "
                f"Contract has {len(self.contract_functions)} functions but doesn't inherit from any base contracts. "
                f"Consider using inheritance to share common functionality."
            )
        
        # Rule 5: Functions with too many responsibilities
        for func in self.contract_functions:
            if hasattr(func, 'responsibilities') and len(func.responsibilities) > 2:
                self.violations.append(
                    f"❌ Lack of modularity in '{self.current_contract}': "
                    f"Function '{func.name}' handles {len(func.responsibilities)} responsibilities: {', '.join(func.responsibilities)}. "
                    f"Consider splitting into separate functions."
                )
    
    def get_violations(self):
        return self.violations
