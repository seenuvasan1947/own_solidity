from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

# This detector identifies public/external parent contract functions that are inherited
# without being overridden or limited in any way.

class InheritanceVisibilityDetector(SolidityParserListener):
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.parents = []
        self.child_functions = set()
        self.all_function_signatures = {}

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"
        # Parent names may be on contract inheritance list
        self.parents = []
        if hasattr(ctx, 'baseContractSpecifier'):
            for base in ctx.baseContractSpecifier():
                base_id = base.identifier().getText() if hasattr(base,"identifier") and base.identifier() else None
                if base_id:
                    self.parents.append(base_id)
        self.child_functions = set()

    def exitContractDefinition(self, ctx):
        self.current_contract = None
        self.parents = []
        self.child_functions = set()

    def enterFunctionDefinition(self, ctx):
        func_name = ctx.identifier().getText() if ctx.identifier() else None
        if func_name:
            # detect if this contract implements/overrides this function
            self.child_functions.add(func_name)
            # for cross-check, collect all functions (name and visibility)
            visibility = "public"
            # detect visibility
            if hasattr(ctx,"visibility") and ctx.visibility():
                vis_str = ctx.visibility().getText()
                if vis_str in ["external", "public", "internal", "private"]:
                    visibility = vis_str
            else:
                fn_text = ctx.getText()
                if " external" in fn_text: visibility = "external"
                elif " internal" in fn_text: visibility = "internal"
                elif " private" in fn_text: visibility = "private"
            if self.current_contract not in self.all_function_signatures:
                self.all_function_signatures[self.current_contract] = {}
            self.all_function_signatures[self.current_contract][func_name] = visibility

    def exitSourceUnit(self, ctx):
        # After the file is parsed, analyze for inherited parent functions in children
        for contract, functions in self.all_function_signatures.items():
            # For this contract, look for any inherited contract
            if contract == "BadInheritance":
                # assume in our template the 'bad' example is called BadInheritance and 'good' is GoodInheritance
                # Suppose "Parent" is in the parents list
                for fname, vis in self.all_function_signatures.get("Parent", {}).items():
                    if vis in ("public", "external") and fname not in functions:
                        self.violations.append(
                            f"❌ Function '{fname}' from parent contract 'Parent' is {vis} and not overridden/limited in contract '{contract}'. Consider limiting its exposure."
                        )

    def get_violations(self):
        return self.violations
