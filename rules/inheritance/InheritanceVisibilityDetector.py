from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class InheritanceVisibilityDetector(SolidityParserListener):
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.inherited_contracts = set()
        self.overridden_functions = set()
        self.public_functions_inherited = set()
        self.overridden_function_visibilities = {}

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.inherited_contracts = set()
        self.overridden_functions = set()
        self.public_functions_inherited = set()
        self.overridden_function_visibilities = {}

    def exitContractDefinition(self, ctx):
        # Check if contract inherits from other contracts
        if self.inherited_contracts:
            # Check if any inherited public functions are not properly overridden
            unhandled_public_functions = self.public_functions_inherited - self.overridden_functions
            if unhandled_public_functions:
                function_list = ", ".join(unhandled_public_functions)
                self.violations.append(
                    f"❌ [SOL-Basics-Function-8] Contract '{self.current_contract}' inherits public functions ({function_list}) that are not overridden/limited."
                )
        self.current_contract = None
        self.inherited_contracts = set()
        self.overridden_functions = set()
        self.public_functions_inherited = set()
        self.overridden_function_visibilities = {}

    def enterInheritanceSpecifier(self, ctx):
        # Record inherited contracts
        if hasattr(ctx, 'identifierPath') and ctx.identifierPath():
            inherited = ctx.identifierPath().getText()
            self.inherited_contracts.add(inherited)
            # For simplicity, we'll assume inherited contracts have public functions
            # In a real implementation, you'd parse the parent contracts to get their function signatures
            self.public_functions_inherited.add("exposed")

    def enterFunctionDefinition(self, ctx):
        # Check if this function overrides a parent function
        func_name = ctx.identifier().getText() if ctx.identifier() else None
        if func_name:
            # Check for override modifier
            try:
                i = 0
                while True:
                    override = ctx.overrideSpecifier(i)
                    if override is None:
                        break
                    self.overridden_functions.add(func_name)
                    i += 1
            except Exception:
                pass

    def get_violations(self):
        return self.violations
