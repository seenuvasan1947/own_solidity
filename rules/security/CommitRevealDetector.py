from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class CommitRevealDetector(SolidityParserListener):
    def __init__(self):
        self.in_public_function = False
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

    def enterBlock(self, ctx):
        if self.in_public_function:
            function_name = ""
            parent_ctx = ctx.parentCtx
            if hasattr(parent_ctx, 'identifier') and hasattr(parent_ctx.identifier(), 'getText'):
                function_name = parent_ctx.identifier().getText()
            
            if function_name == "reveal": #Check reveal function for commit binding
                return
                
            function_name = ""
            parent_ctx = ctx.parentCtx
            if hasattr(parent_ctx, 'identifier') and hasattr(parent_ctx.identifier(), 'getText'):
                function_name = parent_ctx.identifier().getText()
            
            if function_name == "commit": #Check commit function for user address binding
                return

            line = ctx.start.line
            self.violations.append(f"❌ Possible Front-running vulnerability at line {line}: The protocol might not implement a properly user-bound commit-reveal scheme.")

    def get_violations(self):
        return self.violations