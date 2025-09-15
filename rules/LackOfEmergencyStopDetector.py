from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class LackOfEmergencyStopDetector(SolidityParserListener):
    """
    Detector for SCWE-014: Lack of Emergency Stop Mechanism
    Rule Code: 014
    
    Detects contracts that lack emergency stop mechanisms for critical functions.
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.current_function = None
        self.contract_functions = {}  # contract_name -> list of function info
        self.has_pausable = {}  # contract_name -> bool
        self.has_emergency_functions = {}  # contract_name -> bool
        self.critical_functions = {}  # contract_name -> list of critical functions
        
        # Keywords that indicate critical functions
        self.critical_keywords = [
            'transfer', 'withdraw', 'deposit', 'mint', 'burn', 'swap',
            'trade', 'liquidity', 'stake', 'unstake', 'claim', 'redeem',
            'update', 'set', 'change', 'modify', 'configure', 'execute',
            'approve', 'revoke', 'freeze', 'unfreeze'
        ]
        
        # Emergency stop patterns
        self.emergency_patterns = [
            'pause', 'unpause', 'emergency', 'stop', 'halt', 'freeze',
            'whenNotPaused', 'whenPaused', 'pausable', 'emergencyStop',
            'resume', 'restart', 'unfreeze'
        ]
        
        # Pausable contract patterns
        self.pausable_patterns = [
            'Pausable', 'pausable', 'whenNotPaused', 'whenPaused',
            '_pause', '_unpause', 'paused()', 'pause()', 'unpause()'
        ]
    
    def enterContractDefinition(self, ctx):
        """Track contract definitions and initialize data structures."""
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "UnknownContract"
        self.contract_functions[self.current_contract] = []
        self.has_pausable[self.current_contract] = False
        self.has_emergency_functions[self.current_contract] = False
        self.critical_functions[self.current_contract] = []
    
    def exitContractDefinition(self, ctx):
        """Analyze emergency stop mechanisms after processing the contract."""
        if self.current_contract:
            self._analyze_emergency_stop()
        self.current_contract = None
    
    def enterInheritanceSpecifier(self, ctx):
        """Check for Pausable inheritance."""
        if not self.current_contract:
            return
            
        parent_name = ctx.identifierPath().getText() if ctx.identifierPath() else ""
        if 'Pausable' in parent_name or 'pausable' in parent_name.lower():
            self.has_pausable[self.current_contract] = True
    
    def enterFunctionDefinition(self, ctx):
        """Track function definitions and analyze critical functions."""
        if not self.current_contract:
            return
            
        func_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.current_function = func_name
        
        # Check if this is a critical function
        is_critical = self._is_critical_function(func_name)
        
        # Check for emergency stop patterns in function name
        has_emergency_pattern = any(pattern in func_name.lower() for pattern in self.emergency_patterns)
        
        # Check for pausable modifiers
        has_pausable_modifier = False
        for child in ctx.children:
            if hasattr(child, 'getText') and 'whenNotPaused' in child.getText():
                has_pausable_modifier = True
                break
        
        function_info = {
            'name': func_name,
            'line': ctx.start.line,
            'is_critical': is_critical,
            'has_emergency_pattern': has_emergency_pattern,
            'has_pausable_modifier': has_pausable_modifier
        }
        
        self.contract_functions[self.current_contract].append(function_info)
        
        if is_critical:
            self.critical_functions[self.current_contract].append(function_info)
        
        if has_emergency_pattern:
            self.has_emergency_functions[self.current_contract] = True
    
    def enterExpressionStatement(self, ctx):
        """Check for emergency stop patterns in function bodies."""
        if not self.current_function or not self.current_contract:
            return
            
        expr_text = ctx.getText()
        
        # Check for emergency stop patterns
        for pattern in self.emergency_patterns:
            if pattern in expr_text.lower():
                self.has_emergency_functions[self.current_contract] = True
                break
    
    def enterMemberAccess(self, ctx):
        """Check for pausable method calls."""
        if not self.current_function or not self.current_contract:
            return
            
        member_name = ctx.identifier().getText() if ctx.identifier() else ""
        if member_name in ['pause', 'unpause', '_pause', '_unpause']:
            self.has_emergency_functions[self.current_contract] = True
    
    def _is_critical_function(self, func_name):
        """Check if function name suggests critical operations."""
        func_lower = func_name.lower()
        return any(keyword in func_lower for keyword in self.critical_keywords)
    
    def _analyze_emergency_stop(self):
        """Analyze if contract has proper emergency stop mechanisms."""
        if not self.current_contract:
            return
        
        # Check if contract has critical functions
        critical_funcs = self.critical_functions.get(self.current_contract, [])
        if not critical_funcs:
            return
        
        # Check if contract has emergency stop mechanisms
        has_pausable_inheritance = self.has_pausable.get(self.current_contract, False)
        has_emergency_funcs = self.has_emergency_functions.get(self.current_contract, False)
        
        # Check if critical functions have pausable modifiers
        critical_with_pausable = 0
        for func in critical_funcs:
            if func['has_pausable_modifier']:
                critical_with_pausable += 1
        
        # If contract has critical functions but lacks emergency stop mechanisms
        if not has_pausable_inheritance and not has_emergency_funcs:
            violation = {
                'type': 'SCWE-014',
                'contract': self.current_contract,
                'function': 'N/A',
                'line': 0,
                'message': f"Contract '{self.current_contract}' lacks emergency stop mechanism for {len(critical_funcs)} critical functions"
            }
            self.violations.append(violation)
        
        # If contract has pausable inheritance but critical functions don't use it
        elif has_pausable_inheritance and critical_with_pausable == 0:
            violation = {
                'type': 'SCWE-014',
                'contract': self.current_contract,
                'function': 'N/A',
                'line': 0,
                'message': f"Contract '{self.current_contract}' inherits Pausable but critical functions don't use whenNotPaused modifier"
            }
            self.violations.append(violation)
    
    def get_violations(self):
        """Return list of detected violations."""
        return self.violations
