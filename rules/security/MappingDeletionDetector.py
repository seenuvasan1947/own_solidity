# S-SEC-027: Mapping Deletion in Struct
# Detects deletion of structs containing mappings
# Mappings inside structs are not deleted, leaving stale data

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class MappingDeletionDetector(SolidityParserListener):
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.structs_with_mappings = set()
        self.struct_vars = {}  # {var_name: struct_type}
        self.in_function = False
        self.function_name = None

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.structs_with_mappings = set()
        self.struct_vars = {}

    def exitContractDefinition(self, ctx):
        self.current_contract = None

    def enterStructDefinition(self, ctx):
        struct_text = ctx.getText()
        struct_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        
        # Check if struct contains mapping
        if 'mapping' in struct_text:
            self.structs_with_mappings.add(struct_name)

    def enterStateVariableDeclaration(self, ctx):
        var_text = ctx.getText()
        
        # Check if variable is of struct type
        for struct_name in self.structs_with_mappings:
            if struct_name in var_text:
                # Extract variable name
                var_match = re.search(rf'{struct_name}\s+(?:public\s+|private\s+|internal\s+)?(\w+)', var_text)
                if var_match:
                    var_name = var_match.group(1)
                    self.struct_vars[var_name] = struct_name

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
        
        # Check for delete operations
        if 'delete' in stmt_text:
            # Check if deleting a struct variable with mapping
            for var_name, struct_type in self.struct_vars.items():
                if re.search(rf'delete\s+{var_name}', stmt_text):
                    self.violations.append(
                        f"⚠️  [S-SEC-027] MEDIUM: Deletion of struct containing mapping in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                        f"Deleting '{var_name}' (type '{struct_type}') does not delete its mapping fields. "
                        f"Use a lock mechanism or manually clear mapping fields instead."
                    )

    def get_violations(self):
        return self.violations
