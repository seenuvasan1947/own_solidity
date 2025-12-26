# S-ATR-006: Missing Inheritance
# Detects contracts that implement interface functions but don't inherit from the interface
# Based on Slither's unimplemented_interface detector
# Impact: INFORMATIONAL | Confidence: HIGH

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class MissingInheritanceDetector(SolidityParserListener):
    """
    Detects contracts that should inherit from an interface but don't.
    
    Issue: If a contract implements all functions of an interface but doesn't
    explicitly inherit from it, it's not following best practices and may
    cause confusion.
    
    Example (Problematic):
        interface ISomething {
            function f1() external returns(uint);
        }
        
        contract Something {  // Should inherit from ISomething
            function f1() external returns(uint) {
                return 42;
            }
        }
    
    Recommendation: Explicitly inherit from interfaces that are implemented.
    
    Note: This is a simplified version. Full implementation requires
    cross-contract analysis which is complex with ANTLR alone.
    """
    
    def __init__(self):
        self.violations = []
        self.interfaces = {}  # name -> functions
        self.contracts = {}  # name -> (functions, inherits)
        self.current_type = None  # 'interface' or 'contract'
        self.current_name = None
        self.current_functions = []
        self.current_inherits = []
    
    def enterInterfaceDefinition(self, ctx):
        self.current_type = 'interface'
        self.current_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.current_functions = []
    
    def exitInterfaceDefinition(self, ctx):
        if self.current_name:
            self.interfaces[self.current_name] = self.current_functions
        self.current_type = None
        self.current_name = None
        self.current_functions = []
    
    def enterContractDefinition(self, ctx):
        self.current_type = 'contract'
        self.current_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.current_functions = []
        self.current_inherits = []
        
        # Check inheritance
        if ctx.inheritanceSpecifierList():
            # Extract inherited contracts/interfaces
            inherit_text = ctx.inheritanceSpecifierList().getText()
            # Simple parsing - split by comma
            self.current_inherits = [i.strip() for i in inherit_text.split(',')]
    
    def exitContractDefinition(self, ctx):
        if self.current_name and self.current_type == 'contract':
            self.contracts[self.current_name] = (self.current_functions, self.current_inherits)
        self.current_type = None
        self.current_name = None
        self.current_functions = []
        self.current_inherits = []
    
    def enterFunctionDefinition(self, ctx):
        if self.current_type:
            func_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
            # Store function signature (simplified)
            self.current_functions.append(func_name)
    
    def get_violations(self):
        # Check if contracts implement interfaces without inheriting
        for contract_name, (contract_funcs, inherits) in self.contracts.items():
            for interface_name, interface_funcs in self.interfaces.items():
                # Skip if already inherits
                if interface_name in inherits:
                    continue
                
                # Check if contract implements all interface functions
                if set(interface_funcs).issubset(set(contract_funcs)):
                    self.violations.append(
                        f"⚠️ [S-ATR-006] Contract '{contract_name}' implements all functions "
                        f"of interface '{interface_name}' but doesn't inherit from it. "
                        f"Consider adding explicit inheritance for clarity."
                    )
        
        return self.violations
