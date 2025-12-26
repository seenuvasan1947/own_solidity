# S-CODE-021: Assert State Change Detection
# Detects assert() calls that modify state
# assert() should be used for invariants, not state changes

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class AssertStateChangeDetector(SolidityParserListener):
    
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
        
        # Detect assert() calls
        if 'assert(' in stmt_text:
            # Check for state changes within assert
            # Patterns: +=, -=, *=, /=, =, ++, --
            state_change_patterns = [
                r'\w+\s*\+=',
                r'\w+\s*-=',
                r'\w+\s*\*=',
                r'\w+\s*/=',
                r'\w+\s*=\s*[^=]',  # Assignment but not ==
                r'\w+\+\+',
                r'\+\+\w+',
                r'\w+--',
                r'--\w+',
            ]
            
            # Extract assert content
            assert_match = re.search(r'assert\s*\((.*)\)', stmt_text)
            if assert_match:
                assert_content = assert_match.group(1)
                
                # Check if any state change pattern exists in assert
                for pattern in state_change_patterns:
                    if re.search(pattern, assert_content):
                        self.violations.append(
                            f"ℹ️  [S-CODE-021] INFO: Assert with state change in function '{self.function_name}' of contract '{self.current_contract}' at line {line}: "
                            f"assert() call contains state-modifying expression. "
                            f"assert() should be used for invariants only. Use require() for state changes."
                        )
                        break

    def get_violations(self):
        return self.violations
