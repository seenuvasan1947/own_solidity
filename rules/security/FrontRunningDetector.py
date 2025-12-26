from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class FrontRunningDetector(SolidityParserListener):
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None
        self.function_start_line = None
        self.function_has_body = False
        self.is_public_or_external = False
        self.modifies_state = False
        self.has_protection = False

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"

    def exitContractDefinition(self, ctx):
        self.current_contract = None

    def enterFunctionDefinition(self, ctx):
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.function_start_line = ctx.start.line
        self.function_has_body = False
        self.is_public_or_external = False
        self.modifies_state = False
        self.has_protection = False
        
        # Check if function is public or external
        self._check_function_visibility(ctx)

    def _check_function_visibility(self, ctx):
        try:
            i = 0
            while True:
                vis = ctx.visibility(i)
                if vis is None:
                    break
                vis_text = vis.getText()
                if vis_text in ['public', 'external']:
                    self.is_public_or_external = True
                    break
                i += 1
        except Exception:
            pass

    def enterModifierInvocation(self, ctx):
        if not self.in_function:
            return
            
        # Check if this modifier is a protection mechanism
        modifier_text = ctx.getText().lower()
        protection_modifiers = [
            "onlyowner", "onlyadmin", "onlyauthorized", "onlyrole",
            "nonreentrant", "whennotpaused", "auth", "authorized"
        ]
        
        if any(pattern in modifier_text for pattern in protection_modifiers):
            self.has_protection = True

    def exitFunctionDefinition(self, ctx):
        # Check for front-running vulnerability
        if (self.is_public_or_external and 
            self.function_has_body and 
            self.modifies_state and 
            not self.has_protection and
            not self._is_constructor(ctx)):
            
            self.violations.append(
                f"❌ [SOL-Basics-Function-3] Potential front-running vulnerability in function '{self.function_name}' of contract '{self.current_contract}' at line {self.function_start_line}: Function modifies state without protection mechanisms."
            )

        self.in_function = False
        self.function_name = None
        self.function_has_body = False
        self.is_public_or_external = False
        self.modifies_state = False
        self.has_protection = False

    def _is_constructor(self, ctx):
        try:
            func_name = ctx.identifier().getText() if ctx.identifier() else ""
            if func_name == "constructor":
                return True
            if func_name == self.current_contract:
                return True
        except Exception:
            pass
        return False

    def enterBlock(self, ctx):
        if self.in_function:
            self.function_has_body = True

    def enterStatement(self, ctx):
        if not self.in_function:
            return
        self._check_statement(ctx.getText())

    def enterExpressionStatement(self, ctx):
        if not self.in_function:
            return
        self._check_statement(ctx.getText())

    def _check_statement(self, text):
        # Check for state modifications
        state_modification_patterns = [
            "=",  # assignment
            "+=", "-=", "*=", "/=", "%=",  # compound assignments
            "++", "--",  # increment/decrement
            "delete",  # delete keyword
            ".push(", ".pop()",  # array operations
            "transfer(", "send(", "call(",  # value transfers
        ]
        
        if any(pattern in text for pattern in state_modification_patterns):
            self.modifies_state = True

        # Check for protection mechanisms
        protection_patterns = [
            "require(", "assert(", "revert(",
            "onlyOwner", "onlyAdmin", "onlyRole",
            "nonReentrant", "whenNotPaused",
            "msg.sender == owner",
            "hasRole(",
        ]
        
        if any(pattern in text for pattern in protection_patterns):
            self.has_protection = True

    def get_violations(self):
        return self.violations