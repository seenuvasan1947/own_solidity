# S-CODE-024: Deprecated Solidity Standards
# Detects usage of deprecated Solidity functions and keywords
# Using deprecated features can lead to unexpected behavior

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class DeprecatedStandardsDetector(SolidityParserListener):
    
    DEPRECATED_PATTERNS = [
        ('block.blockhash', 'blockhash()', 'Use blockhash() instead'),
        ('msg.gas', 'gasleft()', 'Use gasleft() instead'),
        ('suicide', 'selfdestruct()', 'Use selfdestruct() instead'),
        ('sha3', 'keccak256()', 'Use keccak256() instead'),
        ('throw', 'revert()', 'Use revert() instead'),
        ('.callcode(', '.delegatecall(', 'Use delegatecall() instead'),
        ('constant', 'view/pure', 'Use view or pure instead of constant'),
    ]
    
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
        
        # Check for deprecated 'constant' modifier
        func_text = ctx.getText()
        if re.search(r'\bconstant\b', func_text) and 'view' not in func_text and 'pure' not in func_text:
            self.violations.append(
                f"ℹ️  [S-CODE-024] INFO: Deprecated 'constant' modifier in function '{self.function_name}' of contract '{self.current_contract}' at line {ctx.start.line}: "
                f"Use 'view' or 'pure' instead of 'constant'."
            )

    def exitFunctionDefinition(self, ctx):
        self.in_function = False
        self.function_name = None

    def enterStatement(self, ctx):
        if not self.in_function:
            return
        
        stmt_text = ctx.getText()
        line = ctx.start.line
        
        # Check for deprecated patterns
        if 'block.blockhash' in stmt_text:
            self.violations.append(
                f"ℹ️  [S-CODE-024] INFO: Deprecated 'block.blockhash' in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                f"Use blockhash() instead."
            )
        
        if 'msg.gas' in stmt_text:
            self.violations.append(
                f"ℹ️  [S-CODE-024] INFO: Deprecated 'msg.gas' in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                f"Use gasleft() instead."
            )
        
        if re.search(r'\bsuicide\s*\(', stmt_text):
            self.violations.append(
                f"ℹ️  [S-CODE-024] INFO: Deprecated 'suicide()' in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                f"Use selfdestruct() instead."
            )
        
        if re.search(r'\bsha3\s*\(', stmt_text):
            self.violations.append(
                f"ℹ️  [S-CODE-024] INFO: Deprecated 'sha3()' in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                f"Use keccak256() instead."
            )
        
        if re.search(r'\bthrow\b', stmt_text):
            self.violations.append(
                f"ℹ️  [S-CODE-024] INFO: Deprecated 'throw' in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                f"Use revert() instead."
            )
        
        if '.callcode(' in stmt_text:
            self.violations.append(
                f"ℹ️  [S-CODE-024] INFO: Deprecated 'callcode()' in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                f"Use delegatecall() instead."
            )

    def get_violations(self):
        return self.violations
