from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class AccessControlActorsDetector(SolidityParserListener):
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None
        self.found_access_control = False

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"

    def exitContractDefinition(self, ctx):
        self.current_contract = None

    def enterFunctionDefinition(self, ctx):
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.found_access_control = False

    def exitFunctionDefinition(self, ctx):
        # If no access control check found inside a function that changes state, report
        if not self.found_access_control:
            # Heuristic: flag function if it is "public" or "external" and not a constructor / fallback
            visibility = self._get_function_visibility(ctx)
            if visibility in ['public', 'external'] and not self._is_constructor(ctx):
                line = ctx.start.line
                self.violations.append(
                    f"❌ Unclear actor access control in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: No explicit access control check found."
                )
        self.in_function = False
        self.function_name = None
        self.found_access_control = False

    def enterModifierInvocation(self, ctx):
        if not self.in_function:
            return
            
        # Check if this modifier is an access control modifier
        modifier_text = ctx.getText().lower()
        access_control_modifiers = [
            "onlyowner",
            "onlyadmin", 
            "onlyauthorized",
            "onlyrole",
            "hasrole",
            "requireowner",
            "requireadmin",
            "auth",
            "authorized"
        ]
        
        if any(pattern in modifier_text for pattern in access_control_modifiers):
            self.found_access_control = True

    def enterExpressionStatement(self, ctx):
        if not self.in_function:
            return

        expr_text = ctx.getText()

        # Look for common actor validation patterns
        access_patterns = [
            "msg.sender",
            "require(msg.sender",
            "msg.sender ==",
            "onlyOwner",  # common modifier name
            "onlyAdmin",
            "hasRole(",
            "modifier",  # in general, we usually track via modifiers - but this depends on parsing them differently
        ]

        if any(pattern in expr_text for pattern in access_patterns):
            self.found_access_control = True

    def _get_function_visibility(self, ctx):
        # Check all visibility specifiers in the function definition
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
            # If no explicit visibility, default is "public" for functions in Solidity
            return "public"
        except Exception:
            return "public"

    def _is_constructor(self, ctx):
        # Solidity constructor method names can vary based on version:
        # constructor keyword (since 0.4.22), or same name as contract (older)
        # Check if function is constructor
        try:
            func_name = ctx.identifier().getText() if ctx.identifier() else ""
            if func_name == "constructor":
                return True
            if func_name == self.current_contract:
                return True
        except Exception:
            pass
        return False

    def get_violations(self):
        return self.violations
