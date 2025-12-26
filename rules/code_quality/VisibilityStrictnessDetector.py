from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class VisibilityStrictnessDetector(SolidityParserListener):
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.function_visibilities = {}  # function name -> visibility
        self.function_lines = {}         # function name -> line
        self.function_called_by = {}     # function name -> set of callers
        self.function_defined = set()    # function names defined in this contract
        self.public_functions = set()    # function names that are public/external
        self.current_function = None

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"

    def exitContractDefinition(self, ctx):
        # At the end of the contract, check for unnecessary public/external
        for func, vis in self.function_visibilities.items():
            if vis in ["public", "external"] and func in self.function_defined:
                callers = self.function_called_by.get(func, set())
                # If all callers are internal/private or there are no callers, flag it
                if not any(caller in self.public_functions for caller in callers):
                    line = self.function_lines.get(func, "?")
                    self.violations.append(
                        f"❌ [SOL-Basics-Function-7] Function '{func}' of contract '{self.current_contract}' at line {line} is '{vis}' but is only called internally. Consider making it 'internal' or 'private'."
                    )
        self.function_visibilities = {}
        self.function_lines = {}
        self.function_called_by = {}
        self.function_defined = set()
        self.public_functions = set()
        self.current_function = None
        self.current_contract = None

    def enterFunctionDefinition(self, ctx):
        func_name = ctx.identifier().getText() if ctx.identifier() else None
        if func_name:
            vis = self._get_function_visibility(ctx)
            self.function_visibilities[func_name] = vis
            self.function_lines[func_name] = ctx.start.line
            self.function_defined.add(func_name)
            if vis in ["public", "external"]:
                self.public_functions.add(func_name)
            self.current_function = func_name

    def exitFunctionDefinition(self, ctx):
        self.current_function = None

    def _get_function_visibility(self, ctx):
        try:
            i = 0
            while True:
                vis = ctx.visibility(i)
                if vis is None:
                    break
                vis_text = vis.getText()
                if vis_text in ['public', 'external', 'internal', 'private']:
                    return vis_text
                i += 1
            return "public"  # Solidity default
        except Exception:
            return "public"

    def enterFunctionCall(self, ctx):
        # Record the function name being called and who called it
        try:
            if hasattr(ctx, 'expression') and ctx.expression():
                expr = ctx.expression()
                if hasattr(expr, 'getText'):
                    called = expr.getText()
                    if called not in self.function_called_by:
                        self.function_called_by[called] = set()
                    if self.current_function:
                        self.function_called_by[called].add(self.current_function)
        except Exception:
            pass

    def get_violations(self):
        return self.violations 