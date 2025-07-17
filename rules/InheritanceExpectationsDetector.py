from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class InheritanceExpectationsDetector(SolidityParserListener):
    def __init__(self):
        self.violations = []
        self.contract_parents = {}       # contract_name: [parent1, parent2] 
        self.contract_functions = {}     # contract_name: {funcname: visibility}
        self.current_contract = None
        self.comment_expected_funcs = {} # contract_name: [expected_funcs] 
        self.expected_funcs = {}         # parent: [funcs]
        self.token_stream = None

    def set_token_stream(self, token_stream):
        self.token_stream = token_stream

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.contract_parents[self.current_contract] = []
        
        # Get parent contracts - check for inheritance specifiers
        if hasattr(ctx, 'inheritanceSpecifier') and ctx.inheritanceSpecifier():
            for inheritance in ctx.inheritanceSpecifier():
                if hasattr(inheritance, 'identifierPath') and inheritance.identifierPath():
                    parent_name = inheritance.identifierPath().getText()
                    self.contract_parents[self.current_contract].append(parent_name)
        
        self.contract_functions[self.current_contract] = {}

        # Check for expected functions in comments above this contract
        if self.token_stream:
            self._check_comments_for_expected_functions(ctx, self.current_contract)

    def _check_comments_for_expected_functions(self, ctx, contract_name):
        """Check comments above the contract for expected function declarations"""
        if not self.token_stream:
            return
            
        # Find the contract token position - look for the contract name directly
        contract_token_index = -1
        for i, token in enumerate(self.token_stream.tokens):
            if token.text == contract_name:
                # Check if this is actually a contract definition (look for 'contract' before it)
                for j in range(max(0, i-5), i):
                    if self.token_stream.tokens[j].text == "contract":
                        contract_token_index = j
                        break
                if contract_token_index != -1:
                    break
        
        if contract_token_index == -1:
            return
            
        # Look backwards for comments before the contract
        for i in range(contract_token_index - 1, max(0, contract_token_index - 20), -1):
            token = self.token_stream.tokens[i]
            if token.channel == 1:  # Comment channel
                if token.text.startswith('/**'):
                    # Look for expected_func pattern
                    match = re.search(r'expected_func:\s*([a-zA-Z0-9_, ]+)', token.text)
                    if match:
                        funcs = [f.strip() for f in match.group(1).split(',')]
                        self.comment_expected_funcs[contract_name] = funcs
                        break

    def exitContractDefinition(self, ctx):
        self.current_contract = None

    def enterFunctionDefinition(self, ctx):
        func_name = ctx.identifier().getText() if ctx.identifier() else None
        if func_name and self.current_contract:
            self.contract_functions[self.current_contract][func_name] = "implemented"

    def exitSourceUnit(self, ctx):
        # For every contract, check if expected functions are implemented
        for contract in self.contract_functions:
            # Check comment-expected functions
            missing_comment_funcs = []
            for func in self.comment_expected_funcs.get(contract, []):
                if func not in self.contract_functions.get(contract, {}):
                    missing_comment_funcs.append(func)
            if missing_comment_funcs:
                funcs_str = ", ".join(missing_comment_funcs)
                self.violations.append(
                    f"❌ Contract '{contract}' is expected to implement functions: [{funcs_str}] (from contract comment), but they are missing."
                )

            # Check parent-expected functions (inherited from parent contracts)
            for parent in self.contract_parents.get(contract, []):
                missing_parent_funcs = []
                for func in self.comment_expected_funcs.get(parent, []):
                    if func not in self.contract_functions.get(contract, {}):
                        missing_parent_funcs.append(func)
                if missing_parent_funcs:
                    funcs_str = ", ".join(missing_parent_funcs)
                    self.violations.append(
                        f"❌ Contract '{contract}' is expected to implement functions: [{funcs_str}] (from parent contract '{parent}' comment), but they are missing."
                    )

    def get_violations(self):
        return self.violations
