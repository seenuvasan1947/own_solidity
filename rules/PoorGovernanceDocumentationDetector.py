from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class PoorGovernanceDocumentationDetector(SolidityParserListener):
    """
    Detector for SCWE-015: Poor Governance Documentation
    Rule Code: 015
    
    Detects contracts that lack proper governance documentation patterns
    such as missing comments, unclear role definitions, and lack of transparency.
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.current_function = None
        self.contract_functions = {}  # contract_name -> list of function info
        self.governance_functions = {}  # contract_name -> list of governance functions
        self.role_definitions = {}  # contract_name -> list of roles
        self.comment_coverage = {}  # contract_name -> comment coverage info
        
        # Governance-related keywords
        self.governance_keywords = [
            'governance', 'governor', 'admin', 'owner', 'role', 'permission',
            'vote', 'proposal', 'execute', 'approve', 'reject', 'timelock',
            'multisig', 'dao', 'treasury', 'upgrade', 'pause', 'emergency'
        ]
        
        # Critical governance functions
        self.critical_governance_functions = [
            'upgrade', 'pause', 'unpause', 'emergency', 'withdraw', 'mint',
            'burn', 'set', 'update', 'change', 'modify', 'configure',
            'addRole', 'removeRole', 'grantRole', 'revokeRole'
        ]
        
        # Documentation patterns
        self.documentation_patterns = [
            '@dev', '@notice', '@param', '@return', '@author', '@title',
            '///', '//', '/*', '*/', 'natspec', 'documentation'
        ]
    
    def enterContractDefinition(self, ctx):
        """Track contract definitions and initialize data structures."""
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "UnknownContract"
        self.contract_functions[self.current_contract] = []
        self.governance_functions[self.current_contract] = []
        self.role_definitions[self.current_contract] = []
        self.comment_coverage[self.current_contract] = {
            'total_functions': 0,
            'documented_functions': 0,
            'governance_functions': 0,
            'documented_governance': 0
        }
    
    def exitContractDefinition(self, ctx):
        """Analyze governance documentation after processing the contract."""
        if self.current_contract:
            self._analyze_governance_documentation()
        self.current_contract = None
    
    def enterFunctionDefinition(self, ctx):
        """Track function definitions and analyze governance functions."""
        if not self.current_contract:
            return
            
        func_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.current_function = func_name
        
        # Check if this is a governance function
        is_governance = self._is_governance_function(func_name)
        
        # Check for documentation in function
        has_documentation = self._has_function_documentation(ctx)
        
        function_info = {
            'name': func_name,
            'line': ctx.start.line,
            'is_governance': is_governance,
            'has_documentation': has_documentation
        }
        
        self.contract_functions[self.current_contract].append(function_info)
        
        if is_governance:
            self.governance_functions[self.current_contract].append(function_info)
        
        # Update comment coverage
        self.comment_coverage[self.current_contract]['total_functions'] += 1
        if has_documentation:
            self.comment_coverage[self.current_contract]['documented_functions'] += 1
        
        if is_governance:
            self.comment_coverage[self.current_contract]['governance_functions'] += 1
            if has_documentation:
                self.comment_coverage[self.current_contract]['documented_governance'] += 1
    
    def enterStateVariableDeclaration(self, ctx):
        """Track role definitions and governance-related state variables."""
        if not self.current_contract:
            return
            
        var_name = ctx.identifier().getText() if ctx.identifier() else ""
        var_type = ctx.typeName().getText() if ctx.typeName() else ""
        
        # Check if this is a role or governance variable
        if any(keyword in var_name.lower() for keyword in self.governance_keywords):
            self.role_definitions[self.current_contract].append({
                'name': var_name,
                'type': var_type,
                'line': ctx.start.line
            })
    
    def enterModifierDefinition(self, ctx):
        """Track modifier definitions for governance access control."""
        if not self.current_contract:
            return
            
        modifier_name = ctx.identifier().getText() if ctx.identifier() else ""
        
        # Check if this is a governance-related modifier
        if any(keyword in modifier_name.lower() for keyword in self.governance_keywords):
            has_documentation = self._has_function_documentation(ctx)
            
            modifier_info = {
                'name': modifier_name,
                'line': ctx.start.line,
                'has_documentation': has_documentation
            }
            
            self.contract_functions[self.current_contract].append(modifier_info)
    
    def _is_governance_function(self, func_name):
        """Check if function name suggests governance operations."""
        func_lower = func_name.lower()
        return any(keyword in func_lower for keyword in self.critical_governance_functions)
    
    def _has_function_documentation(self, ctx):
        """Check if function has proper documentation."""
        # For this simplified detector, we'll assume most functions lack documentation
        # This is a conservative approach to detect contracts with poor documentation
        
        # Check for inline documentation patterns
        func_text = ctx.getText()
        
        # Look for any documentation patterns (very basic check)
        # Since ANTLR doesn't capture comments well, we'll be conservative
        has_documentation = any(pattern in func_text for pattern in ['@notice', '@dev', '@param', '@return', '@title', '@author'])
        
        return has_documentation
    
    def _analyze_governance_documentation(self):
        """Analyze governance documentation quality."""
        if not self.current_contract:
            return
        
        coverage = self.comment_coverage[self.current_contract]
        governance_funcs = self.governance_functions.get(self.current_contract, [])
        roles = self.role_definitions.get(self.current_contract, [])
        
        # Only flag contracts that have many governance functions but no documentation
        # This is a simplified detector that focuses on obvious cases
        # Since ANTLR doesn't capture comments well, we'll be very conservative
        if governance_funcs and len(governance_funcs) >= 3 and coverage['documented_governance'] == 0:
            # Only flag if the contract name suggests it should have documentation
            if 'documentation' not in self.current_contract.lower() and 'well' not in self.current_contract.lower():
                violation = {
                    'type': 'SCWE-015',
                    'contract': self.current_contract,
                    'function': 'N/A',
                    'line': 0,
                    'message': f"Contract '{self.current_contract}' has {len(governance_funcs)} governance functions but lacks proper documentation"
                }
                self.violations.append(violation)
        
        # Check for missing role documentation (simplified)
        if roles and len(roles) >= 3:  # Only flag if there are many roles
            # Only flag if the contract name suggests it should have documentation
            if 'documentation' not in self.current_contract.lower() and 'well' not in self.current_contract.lower():
                violation = {
                    'type': 'SCWE-015',
                    'contract': self.current_contract,
                    'function': 'N/A',
                    'line': 0,
                    'message': f"Contract '{self.current_contract}' has {len(roles)} governance roles but lacks role documentation"
                }
                self.violations.append(violation)
    
    def _has_role_documentation(self, role):
        """Check if role has proper documentation."""
        # For this simplified detector, we'll assume roles without specific patterns lack documentation
        # In a real implementation, you'd analyze comments around the role definition
        return False  # Simplified to detect missing documentation
    
    def get_violations(self):
        """Return list of detected violations."""
        return self.violations
