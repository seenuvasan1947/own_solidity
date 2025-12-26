from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class EOAContractCallerDetector(SolidityParserListener):
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None
        self.function_start_line = None

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"

    def exitContractDefinition(self, ctx):
        self.current_contract = None

    def enterFunctionDefinition(self, ctx):
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.function_start_line = ctx.start.line

    def exitFunctionDefinition(self, ctx):
        self.in_function = False
        self.function_name = None
        self.function_start_line = None

    def enterExpressionStatement(self, ctx):
        if not self.in_function:
            return

        text = ctx.getText()
        # Detect restriction to EOA only
        if "msg.sender" in text and "tx.origin" in text:
            if "==" in text or "!=" in text:
                line = ctx.start.line
                self.violations.append(
                    f"⚠️ Function '{self.function_name}' in contract '{self.current_contract}' at line {line} restricts to only EOA or only contracts using msg.sender/tx.origin logic. See references for why this can be problematic."
                )
        # Detect use of isContract pattern
        elif ("isContract(" in text or "address(" in text) and "msg.sender" in text:
            if "require" in text or "if(" in text:
                line = ctx.start.line
                self.violations.append(
                    f"⚠️ Function '{self.function_name}' in contract '{self.current_contract}' at line {line} restricts access based on contract detection (e.g., isContract). This check is often unreliable. See references."
                )

    def get_violations(self):
        return self.violations
