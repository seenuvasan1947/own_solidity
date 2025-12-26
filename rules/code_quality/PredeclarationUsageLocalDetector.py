# S-CODE-035: Predeclaration Usage Local
# Detects local variables used before declaration
# Can cause unexpected behavior (Solidity 0.4.x issue)

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class PredeclarationUsageLocalDetector(SolidityParserListener):
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None
        self.declared_vars = set()
        self.function_body = []

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"

    def exitContractDefinition(self, ctx):
        self.current_contract = None

    def enterFunctionDefinition(self, ctx):
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.declared_vars = set()
        self.function_body = []
        
        # Add function parameters to declared vars
        func_text = ctx.getText()
        params = re.findall(r'\w+\s+(\w+)(?:\s*,|\s*\))', func_text)
        self.declared_vars.update(params)

    def exitFunctionDefinition(self, ctx):
        self._analyze_usage()
        self.in_function = False
        self.function_name = None

    def enterStatement(self, ctx):
        if self.in_function:
            stmt_text = ctx.getText()
            line = ctx.start.line
            self.function_body.append((line, stmt_text))

    def _analyze_usage(self):
        """Analyze function body for pre-declaration usage"""
        declared_in_scope = set(self.declared_vars)
        
        for line, stmt in self.function_body:
            # Check for variable usage
            used_vars = re.findall(r'\b([a-z_]\w*)\b', stmt)
            
            for var in used_vars:
                # Skip keywords and common identifiers
                if var in ['uint', 'uint256', 'int', 'address', 'bool', 'bytes', 'string', 
                          'memory', 'storage', 'calldata', 'public', 'private', 'internal',
                          'external', 'view', 'pure', 'payable', 'if', 'else', 'for', 'while',
                          'return', 'require', 'assert', 'revert', 'emit', 'new', 'delete']:
                    continue
                
                # Check if variable is used before declaration
                if var not in declared_in_scope:
                    # Check if it's declared later in the function
                    is_declared_later = any(re.search(rf'\b(uint|uint256|int|address|bool|bytes\d*|string)\s+{var}\b', s) 
                                          for l, s in self.function_body if l > line)
                    
                    if is_declared_later:
                        self.violations.append(
                            f"⚠️  [S-CODE-035] LOW: Variable used before declaration in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                            f"Variable '{var}' is used before its declaration. "
                            f"Move declaration before usage."
                        )
            
            # Track variable declarations
            var_decls = re.findall(r'\b(?:uint|uint256|int|address|bool|bytes\d*|string)\s+(\w+)', stmt)
            declared_in_scope.update(var_decls)

    def get_violations(self):
        return self.violations
