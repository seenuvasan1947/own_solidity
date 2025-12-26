# S-CODE-014: Void Constructor Call
# Detects constructor calls to base contracts that have no implementation
# Calling empty constructors can be misleading and waste gas

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class VoidConstructorDetector(SolidityParserListener):
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.contracts_with_constructors = {}  # {contract_name: has_body}
        self.in_constructor = False
        self.constructor_line = None

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"

    def exitContractDefinition(self, ctx):
        self.current_contract = None

    def enterConstructorDefinition(self, ctx):
        self.in_constructor = True
        self.constructor_line = ctx.start.line
        
        # Check if constructor has a body with actual code
        constructor_text = ctx.getText()
        
        # Extract constructor body
        body_match = re.search(r'\{([^}]*)\}', constructor_text)
        if body_match:
            body = body_match.group(1).strip()
            # Check if body is empty or only has whitespace/comments
            has_body = len(body) > 0 and not re.match(r'^\s*$', body)
            self.contracts_with_constructors[self.current_contract] = has_body
        else:
            self.contracts_with_constructors[self.current_contract] = False
        
        # Check for base constructor calls
        self._check_base_constructor_calls(constructor_text)

    def exitConstructorDefinition(self, ctx):
        self.in_constructor = False
        self.constructor_line = None

    def _check_base_constructor_calls(self, constructor_text):
        """Check if constructor calls base constructors that are empty"""
        # Pattern: BaseContract() in constructor modifiers
        base_calls = re.finditer(r'(\w+)\s*\(\s*\)', constructor_text)
        
        for match in base_calls:
            base_contract = match.group(1)
            
            # Skip if it's not a contract name (e.g., constructor keyword)
            if base_contract.lower() in ['constructor', 'public', 'internal', 'private']:
                continue
            
            # Check if this base contract has an empty constructor
            if base_contract in self.contracts_with_constructors:
                if not self.contracts_with_constructors[base_contract]:
                    self.violations.append(
                        f"⚠️  [S-CODE-014] LOW: Void constructor call in contract '{self.current_contract}' at line {self.constructor_line}: "
                        f"Calling empty constructor of base contract '{base_contract}'. "
                        f"Remove the call to avoid confusion and save gas."
                    )

    def get_violations(self):
        return self.violations
