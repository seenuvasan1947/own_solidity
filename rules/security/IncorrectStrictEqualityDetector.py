# S-SEC-026: Incorrect Strict Equality
# Detects dangerous strict equality checks on balances or timestamps
# Can be manipulated by attackers to break contract logic

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class IncorrectStrictEqualityDetector(SolidityParserListener):
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None
        self.balance_vars = set()
        self.timestamp_vars = set()

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"

    def exitContractDefinition(self, ctx):
        self.current_contract = None

    def enterFunctionDefinition(self, ctx):
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.balance_vars = set()
        self.timestamp_vars = set()

    def exitFunctionDefinition(self, ctx):
        self.in_function = False
        self.function_name = None

    def enterStatement(self, ctx):
        if not self.in_function:
            return
        
        stmt_text = ctx.getText()
        line = ctx.start.line
        
        # Track balance-related variables
        if '.balance' in stmt_text or 'balanceOf(' in stmt_text:
            var_match = re.search(r'(\w+)\s*=.*balance', stmt_text)
            if var_match:
                self.balance_vars.add(var_match.group(1))
        
        # Track timestamp variables
        if 'block.timestamp' in stmt_text or 'now' in stmt_text or 'block.number' in stmt_text:
            var_match = re.search(r'(\w+)\s*=.*(block\.timestamp|now|block\.number)', stmt_text)
            if var_match:
                self.timestamp_vars.add(var_match.group(1))
        
        # Check for strict equality with balance
        if '==' in stmt_text:
            # Direct balance checks
            if '.balance==' in stmt_text or '==.balance' in stmt_text.replace(' ', ''):
                # Skip address comparisons
                if not re.search(r'address\s*\(.*\)\s*==\s*address', stmt_text):
                    self.violations.append(
                        f"⚠️  [S-SEC-026] MEDIUM: Dangerous strict equality with balance in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                        f"Using == with balance can be manipulated. Use >= or <= instead."
                    )
            
            # Check balance variables
            for var in self.balance_vars:
                if re.search(rf'\b{var}\s*==|\==\s*{var}\b', stmt_text):
                    self.violations.append(
                        f"⚠️  [S-SEC-026] MEDIUM: Dangerous strict equality with balance variable in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                        f"Variable '{var}' holds balance. Using == can be manipulated. Use >= or <= instead."
                    )
            
            # Check timestamp variables
            for var in self.timestamp_vars:
                if re.search(rf'\b{var}\s*==|\==\s*{var}\b', stmt_text):
                    self.violations.append(
                        f"⚠️  [S-SEC-026] MEDIUM: Dangerous strict equality with timestamp in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                        f"Variable '{var}' holds timestamp. Using == can be manipulated. Use >= or <= instead."
                    )

    def get_violations(self):
        return self.violations
