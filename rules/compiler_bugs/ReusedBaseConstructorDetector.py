# S-BUG-006: Reused Base Constructor
# Detects base constructors called multiple times in inheritance hierarchy
# Based on Slither's reused_base_constructor detector
# Impact: MEDIUM | Confidence: MEDIUM

from antlr4 import *
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class ReusedBaseConstructorDetector(SolidityParserListener):
    """
    Detects reused base constructors in inheritance.
    
    Vulnerability: If a base constructor is called from multiple places
    in the inheritance hierarchy, it may execute multiple times or
    cause unexpected behavior.
    
    Example (Problematic):
        contract A {
            constructor(uint x) public { }
        }
        contract B is A {
            constructor() A(2) public { }
        }
        contract C is A {
            constructor() A(3) public { }
        }
        contract D is B, C {  // A's constructor called twice!
            constructor() public { }
        }
    
    Recommendation: Remove duplicate constructor calls.
    """
    
    def __init__(self):
        self.violations = []
        self.contracts = {}  # contract_name -> (inherits, constructor_calls)
        self.current_contract = None
        self.constructor_calls = []
    
    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.constructor_calls = []
        
        # Extract inheritance list
        inherits = []
        if ctx.inheritanceSpecifierList():
            inherit_text = ctx.inheritanceSpecifierList().getText()
            # Parse inheritance with constructor calls
            # Example: A(1), B(2)
            parts = inherit_text.split(',')
            for part in parts:
                if '(' in part:
                    base_name = part.split('(')[0].strip()
                    self.constructor_calls.append(base_name)
                    inherits.append(base_name)
                else:
                    inherits.append(part.strip())
        
        self.contracts[self.current_contract] = (inherits, [])
    
    def enterConstructorDefinition(self, ctx):
        # Check for modifier list (base constructor calls)
        if ctx.modifierList():
            modifier_text = ctx.modifierList().getText()
            # Look for base constructor calls
            for contract_name in self.contracts.keys():
                if f"{contract_name}(" in modifier_text:
                    self.constructor_calls.append(contract_name)
    
    def exitContractDefinition(self, ctx):
        if self.current_contract:
            inherits, _ = self.contracts[self.current_contract]
            self.contracts[self.current_contract] = (inherits, self.constructor_calls)
            
            # Check for duplicate constructor calls
            seen = set()
            for base in self.constructor_calls:
                if base in seen:
                    self.violations.append(
                        f"⚠️ [S-BUG-006] Contract '{self.current_contract}' calls base constructor "
                        f"'{base}' multiple times in inheritance hierarchy. This may cause unexpected behavior."
                    )
                seen.add(base)
        
        self.current_contract = None
        self.constructor_calls = []
    
    def get_violations(self):
        return self.violations
