from antlr4 import * 
from SolidityLexer import SolidityLexer 
from SolidityParser import SolidityParser 
from SolidityParserListener import SolidityParserListener 

class MissingFuncInheritanceDetector(SolidityParserListener):
    def __init__(self):
        self.violations = []
        self.contract_parents = {}       # contract_name: [parent1, parent2]
        self.contract_funcs = {}         # contract_name: set(func1, func2)
        self.parent_required_funcs = {}  # parent_contract: [required_func1, required_func2]
        self.current_contract = None

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"
        # Get inheritance chain
        parents = []
        if hasattr(ctx, "baseContractSpecifier") and ctx.baseContractSpecifier():
            bases = ctx.baseContractSpecifier()
            if not isinstance(bases, list): bases = [bases]
            for base in bases:
                base_id = base.identifier().getText() if hasattr(base,"identifier") else None
                if base_id: parents.append(base_id)
        self.contract_parents[self.current_contract] = parents
        self.contract_funcs[self.current_contract] = set()

    def exitContractDefinition(self, ctx):
        self.current_contract = None

    def enterFunctionDefinition(self, ctx):
        func_name = ctx.identifier().getText() if ctx.identifier() else None
        if func_name and self.current_contract:
            self.contract_funcs[self.current_contract].add(func_name)

    def get_all_parents(self, contract, cache=None):
        if cache is None: cache = set()
        for parent in self.contract_parents.get(contract, []):
            if parent not in cache:
                cache.add(parent)
                self.get_all_parents(parent, cache)
        return cache

    # Example: Pausable parent expects 'pause' and 'unpause',
    # OwnerAdmin expects 'changeAdmin', etc.
    # Customize these as needed for your context.
    def get_required_parent_funcs(self, parent):
        if parent == "Pausable":
            return ["pause", "unpause"]
        elif parent == "OwnerAdmin":
            return ["changeAdmin"]
        else:
            # Add more parent->required-func mappings here
            return []

    def exitSourceUnit(self, ctx):
        for contract in self.contract_parents:
            all_parents = self.get_all_parents(contract)
            for parent in all_parents:
                required_funcs = self.get_required_parent_funcs(parent)
                for func in required_funcs:
                    if func not in self.contract_funcs[contract]:
                        self.violations.append(
                            f"❌ Contract '{contract}' inherits from '{parent}' but does not implement required function '{func}'"
                        )

    def get_violations(self):
        return self.violations
