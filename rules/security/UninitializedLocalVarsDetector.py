# S-SEC-032: Uninitialized Local Variables
# Detects local variables used before initialization
# Can lead to unexpected behavior with zero values

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class UninitializedLocalVarsDetector(SolidityParserListener):
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None
        self.function_body = []
        self.initialized_vars = set()

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"

    def exitContractDefinition(self, ctx):
        self.current_contract = None

    def enterFunctionDefinition(self, ctx):
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.function_body = []
        self.initialized_vars = set()
        
        # Add function parameters as initialized
        func_text = ctx.getText()
        params = re.findall(r'\w+\s+(\w+)(?:\s*,|\s*\))', func_text)
        self.initialized_vars.update(params)

    def exitFunctionDefinition(self, ctx):
        self._analyze_initialization()
        self.in_function = False
        self.function_name = None

    def enterStatement(self, ctx):
        if self.in_function:
            stmt_text = ctx.getText()
            line = ctx.start.line
            self.function_body.append((line, stmt_text))

    def _analyze_initialization(self):
        """Analyze function body for uninitialized variable usage"""
        for line, stmt in self.function_body:
            # Track variable declarations
            decls = re.findall(r'\b(?:uint|uint256|int|address|bool|bytes\d*|string)\s+(\w+)\s*(?:=|;)', stmt)
            for var_name in decls:
                # Check if initialized in declaration
                if re.search(rf'{var_name}\s*=', stmt):
                    self.initialized_vars.add(var_name)
            
            # Check for variable usage
            used_vars = re.findall(r'\b([a-z_]\w*)\b', stmt)
            for var in used_vars:
                # Skip keywords
                if var in ['uint', 'uint256', 'int', 'address', 'bool', 'bytes', 'string',
                          'memory', 'storage', 'if', 'else', 'for', 'while', 'return',
                          'require', 'assert', 'revert', 'emit', 'new', 'delete', 'this', 'msg', 'tx']:
                    continue
                
                # Check if variable is used before initialization
                if var in [d for decl_line, decl_stmt in self.function_body 
                          for d in re.findall(r'\b(?:uint|uint256|int|address|bool|bytes\d*|string)\s+(\w+)', decl_stmt)]:
                    if var not in self.initialized_vars:
                        self.violations.append(
                            f"⚠️  [S-SEC-032] MEDIUM: Uninitialized local variable in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                            f"Variable '{var}' is used before initialization. "
                            f"Initialize variable before use."
                        )
                        # Add to initialized to avoid duplicate reports
                        self.initialized_vars.add(var)
            
            # Track assignments
            assignments = re.findall(r'(\w+)\s*=', stmt)
            self.initialized_vars.update(assignments)

    def get_violations(self):
        return self.violations
