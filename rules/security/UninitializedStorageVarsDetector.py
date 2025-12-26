# S-SEC-034: Uninitialized Storage Variables
# Detects uninitialized storage pointers
# Can override critical state variables

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class UninitializedStorageVarsDetector(SolidityParserListener):
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None
        self.struct_types = set()

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.struct_types = set()

    def exitContractDefinition(self, ctx):
        self.current_contract = None

    def enterStructDefinition(self, ctx):
        struct_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.struct_types.add(struct_name)

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
        
        # Detect uninitialized storage pointers
        # Pattern: StructType storage varName; (without initialization)
        for struct_type in self.struct_types:
            # Check for storage declaration without initialization
            if re.search(rf'\b{struct_type}\s+storage\s+(\w+)\s*;', stmt_text):
                var_match = re.search(rf'{struct_type}\s+storage\s+(\w+)', stmt_text)
                if var_match:
                    var_name = var_match.group(1)
                    self.violations.append(
                        f"❌ [S-SEC-034] HIGH: Uninitialized storage pointer in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                        f"Storage variable '{var_name}' of type '{struct_type}' is not initialized. "
                        f"This will point to storage slot 0 and can override critical state variables. "
                        f"Initialize the storage pointer."
                    )

    def get_violations(self):
        return self.violations
