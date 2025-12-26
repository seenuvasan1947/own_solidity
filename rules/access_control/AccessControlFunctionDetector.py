from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class AccessControlFunctionDetector(SolidityParserListener):
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None
        self.function_start_line = None
        self.is_state_mutability_view_or_pure = False
        self.has_access_control = False
        self.has_state_modification = False

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"

    def exitContractDefinition(self, ctx):
        self.current_contract = None

    def enterFunctionDefinition(self, ctx):
        self.in_function = True
        self.has_access_control = False
        self.has_state_modification = False
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.function_start_line = ctx.start.line
        self.is_state_mutability_view_or_pure = False
        if hasattr(ctx, "stateMutability") and ctx.stateMutability():
            mut = ctx.stateMutability().getText()
            if mut == "view" or mut == "pure":
                self.is_state_mutability_view_or_pure = True
        else:
            fn_text = ctx.getText()
            if " view" in fn_text or " pure" in fn_text:
                self.is_state_mutability_view_or_pure = True

    def exitFunctionDefinition(self, ctx):
        if (
            self.in_function
            and not self.is_state_mutability_view_or_pure
            and self.has_state_modification
            and not self.has_access_control
        ):
            self.violations.append(
                f"❌ Function '{self.function_name}' in contract '{self.current_contract}' at line {self.function_start_line} modifies state with no access control."
            )
        self.in_function = False
        self.function_name = None
        self.function_start_line = None
        self.has_access_control = False
        self.is_state_mutability_view_or_pure = False
        self.has_state_modification = False

    def enterExpressionStatement(self, ctx):
        if not self.in_function or self.is_state_mutability_view_or_pure:
            return
        text = ctx.getText()
        if "=" in text and "==" not in text and not text.startswith("require") and not text.startswith("assert"):
            self.has_state_modification = True
        if ("onlyOwner" in text
            or "onlyAdmin" in text
            or "require(msg.sender" in text
            or "require(owner ==" in text
            or "hasRole(" in text
        ):
            self.has_access_control = True

    def enterModifierInvocation(self, ctx):
        if self.in_function:
            mod_text = ctx.getText()
            if "onlyOwner" in mod_text or "onlyAdmin" in mod_text or "hasRole" in mod_text:
                self.has_access_control = True

    def get_violations(self):
        return self.violations
