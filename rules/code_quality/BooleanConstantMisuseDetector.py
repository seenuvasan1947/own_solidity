# S-CODE-023: Boolean Constant Misuse
# Detects misuse of boolean constants in conditions and expressions
# Indicates dead code or logic errors

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class BooleanConstantMisuseDetector(SolidityParserListener):
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"

    def exitContractDefinition(self, ctx):
        self.current_contract = None

    def enterFunctionDefinition(self, ctx):
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"

    def exitFunctionDefinition(self, ctx):
        self.in_function = False
        self.function_name = None

    def enterStatement(self, ctx):
        if not self.in_function:
            return
        
        stmt_text = ctx.getText()
        line = ctx.start.line
        
        # Detect problematic boolean constant usage
        # 1. if (false) or if (true) - except while(true)
        if re.search(r'if\s*\(\s*false\s*\)', stmt_text):
            self.violations.append(
                f"⚠️  [S-CODE-023] MEDIUM: Boolean constant misuse in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                f"if (false) detected - this is dead code. Remove or fix the condition."
            )
        elif re.search(r'if\s*\(\s*true\s*\)', stmt_text):
            self.violations.append(
                f"⚠️  [S-CODE-023] MEDIUM: Boolean constant misuse in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                f"if (true) detected - condition is always true. Simplify or remove."
            )
        
        # 2. return (x || true) or return (x && false)
        elif re.search(r'\|\|\s*true\b', stmt_text):
            self.violations.append(
                f"⚠️  [S-CODE-023] MEDIUM: Boolean constant misuse in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                f"Expression '|| true' is always true. Simplify the logic."
            )
        elif re.search(r'&&\s*false\b', stmt_text):
            self.violations.append(
                f"⚠️  [S-CODE-023] MEDIUM: Boolean constant misuse in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                f"Expression '&& false' is always false. Simplify the logic."
            )
        
        # 3. require(false) or assert(false)
        elif re.search(r'require\s*\(\s*false\s*\)', stmt_text):
            self.violations.append(
                f"⚠️  [S-CODE-023] MEDIUM: Boolean constant misuse in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                f"require(false) detected - this will always revert. Remove or fix."
            )
        elif re.search(r'assert\s*\(\s*false\s*\)', stmt_text):
            self.violations.append(
                f"⚠️  [S-CODE-023] MEDIUM: Boolean constant misuse in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                f"assert(false) detected - this will always fail. Remove or fix."
            )

    def get_violations(self):
        return self.violations
