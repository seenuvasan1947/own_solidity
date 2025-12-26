# S-CODE-018: Built-in Symbol Shadowing
# Detects shadowing of Solidity built-in symbols and reserved keywords
# Can lead to unexpected behavior and confusion

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class BuiltinSymbolShadowingDetector(SolidityParserListener):
    
    BUILTIN_SYMBOLS = {
        'assert', 'require', 'revert', 'block', 'blockhash', 'gasleft',
        'msg', 'now', 'tx', 'this', 'addmod', 'mulmod', 'keccak256',
        'sha256', 'sha3', 'ripemd160', 'ecrecover', 'selfdestruct',
        'suicide', 'abi', 'fallback', 'receive'
    }
    
    RESERVED_KEYWORDS = {
        'abstract', 'after', 'alias', 'apply', 'auto', 'case', 'catch',
        'copyof', 'default', 'define', 'final', 'immutable', 'implements',
        'in', 'inline', 'let', 'macro', 'match', 'mutable', 'null', 'of',
        'override', 'partial', 'promise', 'reference', 'relocatable',
        'sealed', 'sizeof', 'static', 'supports', 'switch', 'try', 'type',
        'typedef', 'typeof', 'unchecked'
    }
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"

    def exitContractDefinition(self, ctx):
        self.current_contract = None

    def enterStateVariableDeclaration(self, ctx):
        var_text = ctx.getText()
        line = ctx.start.line
        match = re.search(r'\b(\w+)\s*(?:=|;)', var_text)
        if match:
            var_name = match.group(1)
            if var_name in self.BUILTIN_SYMBOLS or var_name in self.RESERVED_KEYWORDS:
                self.violations.append(
                    f"⚠️  [S-CODE-018] LOW: Built-in symbol shadowing in contract '{self.current_contract}' at line {line}: "
                    f"State variable '{var_name}' shadows built-in symbol. "
                    f"Rename to avoid unexpected behavior."
                )

    def enterFunctionDefinition(self, ctx):
        self.in_function = True
        func_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.function_name = func_name
        
        # Check if function name shadows builtin (excluding fallback/receive)
        if func_name in self.BUILTIN_SYMBOLS and func_name not in ['fallback', 'receive']:
            self.violations.append(
                f"⚠️  [S-CODE-018] LOW: Built-in symbol shadowing in contract '{self.current_contract}' at line {ctx.start.line}: "
                f"Function '{func_name}' shadows built-in symbol. "
                f"Rename to avoid confusion."
            )

    def exitFunctionDefinition(self, ctx):
        self.in_function = False
        self.function_name = None

    def enterModifierDefinition(self, ctx):
        modifier_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        if modifier_name in self.BUILTIN_SYMBOLS or modifier_name in self.RESERVED_KEYWORDS:
            self.violations.append(
                f"⚠️  [S-CODE-018] LOW: Built-in symbol shadowing in contract '{self.current_contract}' at line {ctx.start.line}: "
                f"Modifier '{modifier_name}' shadows built-in symbol. "
                f"Rename to avoid confusion."
            )

    def enterEventDefinition(self, ctx):
        event_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        if event_name in self.BUILTIN_SYMBOLS or event_name in self.RESERVED_KEYWORDS:
            self.violations.append(
                f"⚠️  [S-CODE-018] LOW: Built-in symbol shadowing in contract '{self.current_contract}' at line {ctx.start.line}: "
                f"Event '{event_name}' shadows built-in symbol. "
                f"Rename to avoid confusion."
            )

    def enterVariableDeclarationStatement(self, ctx):
        if not self.in_function:
            return
        
        var_text = ctx.getText()
        line = ctx.start.line
        match = re.search(r'\b(\w+)\s*(?:=|;)', var_text)
        if match:
            var_name = match.group(1)
            if var_name in self.BUILTIN_SYMBOLS or var_name in self.RESERVED_KEYWORDS:
                self.violations.append(
                    f"⚠️  [S-CODE-018] LOW: Built-in symbol shadowing in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                    f"Local variable '{var_name}' shadows built-in symbol. "
                    f"Rename to avoid unexpected behavior."
                )

    def get_violations(self):
        return self.violations
