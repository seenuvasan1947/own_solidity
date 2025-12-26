# S-CODE-026: Incorrect Using-For Statement
# Detects using-for statements where library has no matching function
# Confusing and has no effect

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class IncorrectUsingForDetector(SolidityParserListener):
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.libraries = {}  # {lib_name: [function_signatures]}
        self.using_for_statements = []  # [(line, type, library)]

    def enterContractDefinition(self, ctx):
        contract_text = ctx.getText()
        contract_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        
        # Check if it's a library
        if 'library' in contract_text[:50]:  # Check beginning
            self.current_contract = contract_name
            self.libraries[contract_name] = []

    def exitContractDefinition(self, ctx):
        self.current_contract = None

    def enterFunctionDefinition(self, ctx):
        if self.current_contract and self.current_contract in self.libraries:
            # Extract function signature
            func_text = ctx.getText()
            func_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
            
            # Extract first parameter type
            param_match = re.search(r'\(([^)]*)\)', func_text)
            if param_match:
                params = param_match.group(1)
                if params:
                    first_param = params.split(',')[0].strip()
                    param_type = first_param.split()[0] if first_param else None
                    if param_type:
                        self.libraries[self.current_contract].append(param_type)

    def enterUsingForDeclaration(self, ctx):
        using_text = ctx.getText()
        line = ctx.start.line
        
        # Pattern: using LibraryName for Type;
        match = re.search(r'using\s+(\w+)\s+for\s+(\w+)', using_text)
        if match:
            library = match.group(1)
            type_name = match.group(2)
            self.using_for_statements.append((line, type_name, library))

    def check_using_for(self):
        """Check if using-for statements are valid"""
        for line, type_name, library in self.using_for_statements:
            if library in self.libraries:
                # Check if library has function with matching type
                if type_name not in self.libraries[library] and '*' not in self.libraries[library]:
                    self.violations.append(
                        f"ℹ️  [S-CODE-026] INFO: Incorrect using-for statement at line {line}: "
                        f"Library '{library}' has no function with '{type_name}' as first parameter. "
                        f"This statement has no effect."
                    )

    def get_violations(self):
        self.check_using_for()
        return self.violations
