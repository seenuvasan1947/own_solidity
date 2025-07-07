from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class SelfDestructDetector(SolidityParserListener):
    def __init__(self):
        self.in_public_function = False
        self.in_modifier = False
        self.violations = []



    def enterFunctionDefinition(self, ctx):
        # Check all visibility specifiers
        self.in_public_function = False
        i = 0
        while True:
            vis = ctx.visibility(i)
            if vis is None:
                break
            vis_text = vis.getText()
            if vis_text in ["public", "external"]:
                self.in_public_function = True
                break
            i += 1

    def exitFunctionDefinition(self, ctx):
        self.in_public_function = False

    def enterModifierInvocation(self, ctx):
        if ctx.getText().lower() in ["onlyowner", "isowner"]:
            self.in_modifier = True

    def exitModifierInvocation(self, ctx):
        self.in_modifier = False

    def enterFunctionCall(self, ctx):
        if self.in_public_function and not self.in_modifier:
            if ctx.getText().startswith("selfdestruct"):
                line = ctx.start.line
                self.violations.append(f"❌ Unsafe selfdestruct() at line {line}: {ctx.getText()}")

    def get_violations(self):
        return self.violations