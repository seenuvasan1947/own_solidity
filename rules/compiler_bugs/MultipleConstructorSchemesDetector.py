# S-BUG-001: Multiple Constructor Schemes
# Detects contracts with both old and new constructor syntax (pre-0.4.23 issue)
# Based on Slither's multiple_constructor_schemes detector
# Impact: HIGH | Confidence: HIGH

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class MultipleConstructorSchemesDetector(SolidityParserListener):
    """
    Detects contracts with multiple constructor definitions.
    
    Vulnerability: Prior to Solidity 0.4.23, contracts could have both:
    - Old style: function ContractName() { }
    - New style: constructor() { }
    
    If both exist, only the first one executes, which may be unintended.
    
    Example (BAD):
        contract A {
            uint x;
            constructor() public {  // This runs
                x = 0;
            }
            function A() public {  // This is ignored!
                x = 1;
            }
        }
    
    Recommendation: Use only one constructor, preferably the new syntax.
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.contract_line = None
        self.constructors = []  # List of (type, name, line)
    
    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.contract_line = ctx.start.line
        self.constructors = []
    
    def exitContractDefinition(self, ctx):
        # Check if multiple constructors exist
        if len(self.constructors) > 1:
            constructor_info = ", ".join([f"{ctype} at line {line}" for ctype, _, line in self.constructors])
            self.violations.append(
                f"❌ [S-BUG-001] Contract '{self.current_contract}' at line {self.contract_line} "
                f"has multiple constructors: {constructor_info}. "
                f"Only one constructor should be defined. Use the new 'constructor()' syntax."
            )
        
        self.current_contract = None
        self.constructors = []
    
    def enterConstructorDefinition(self, ctx):
        # New-style constructor
        if self.current_contract:
            line = ctx.start.line
            self.constructors.append(("new-style constructor", "constructor", line))
    
    def enterFunctionDefinition(self, ctx):
        # Check for old-style constructor (function with same name as contract)
        if self.current_contract and ctx.identifier():
            func_name = ctx.identifier().getText()
            if func_name == self.current_contract:
                line = ctx.start.line
                self.constructors.append(("old-style constructor", func_name, line))
    
    def get_violations(self):
        return self.violations
