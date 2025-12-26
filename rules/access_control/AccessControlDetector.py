from SolidityParserListener import SolidityParserListener
from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class AccessControlDetector(SolidityParserListener):
    def __init__(self):
        self.violations = []

    def enterFunctionDefinition(self, ctx):
        function_name = ""
        if ctx.identifier():
            function_name = ctx.identifier().getText()

        # Check visibility
        is_public_or_external = False
        for vis in ctx.visibility():
            if vis.getText() in ["public", "external"]:
                is_public_or_external = True
                break

        # Check modifiers
        has_access_control = False
        for modifier in ctx.modifierInvocation():
            mod_text = modifier.getText().lower()
            if "only" in mod_text or "role" in mod_text:
                has_access_control = True
                break

        # Optional: add detection for require(msg.sender == owner) in body (advanced)

        if is_public_or_external and not has_access_control and ctx.body:
            line = ctx.start.line
            self.violations.append(
                f"❌ [Line {line}] Function `{function_name}` lacks access control (public/external with no modifiers)."
            )

    def get_violations(self):
        return self.violations
