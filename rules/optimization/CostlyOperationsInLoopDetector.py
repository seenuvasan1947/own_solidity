# S-OPT-004: Costly Operations in Loop
# Detects state variable modifications inside loops
# SSTORE operations in loops waste significant gas

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class CostlyOperationsInLoopDetector(SolidityParserListener):
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None
        self.loop_depth = 0
        self.state_vars = set()
        self.costly_ops = []

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.state_vars = set()

    def exitContractDefinition(self, ctx):
        self.current_contract = None

    def enterStateVariableDeclaration(self, ctx):
        var_text = ctx.getText()
        match = re.search(r'\b(\w+)\s*(?:=|;)', var_text)
        if match:
            var_name = match.group(1)
            if var_name not in ['uint', 'uint256', 'address', 'bool', 'string', 'bytes', 'mapping']:
                self.state_vars.add(var_name)

    def enterFunctionDefinition(self, ctx):
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.loop_depth = 0
        self.costly_ops = []

    def exitFunctionDefinition(self, ctx):
        if self.costly_ops:
            ops_desc = ', '.join([f"line {line}" for line in self.costly_ops])
            self.violations.append(
                f"ℹ️  [S-OPT-004] INFO: Costly state operations in loop in function '{self.function_name}' of contract '{self.current_contract}': "
                f"State modifications at {ops_desc}. "
                f"Use local variables inside loop and update state once after loop."
            )
        
        self.in_function = False
        self.function_name = None

    def enterForStatement(self, ctx):
        if self.in_function:
            self.loop_depth += 1

    def exitForStatement(self, ctx):
        if self.in_function:
            self.loop_depth -= 1

    def enterWhileStatement(self, ctx):
        if self.in_function:
            self.loop_depth += 1

    def exitWhileStatement(self, ctx):
        if self.in_function:
            self.loop_depth -= 1

    def enterStatement(self, ctx):
        if not self.in_function or self.loop_depth == 0:
            return
        
        stmt_text = ctx.getText()
        line = ctx.start.line
        
        # Check for state variable modifications
        for var in self.state_vars:
            # Patterns: var++, var--, var +=, var -=, var =
            patterns = [
                rf'\b{var}\s*\+\+',
                rf'\+\+\s*{var}\b',
                rf'\b{var}\s*--',
                rf'--\s*{var}\b',
                rf'\b{var}\s*\+=',
                rf'\b{var}\s*-=',
                rf'\b{var}\s*\*=',
                rf'\b{var}\s*/=',
                rf'\b{var}\s*=\s*[^=]',  # Assignment but not ==
            ]
            
            for pattern in patterns:
                if re.search(pattern, stmt_text):
                    self.costly_ops.append(line)
                    break

    def get_violations(self):
        return self.violations
