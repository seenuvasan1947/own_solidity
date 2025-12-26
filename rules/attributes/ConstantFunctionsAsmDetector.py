# S-ATR-001: Constant Functions Using Assembly
# Detects view/pure functions that use assembly code (pre-Solidity 0.5 issue)
# Based on Slither's const_functions_asm detector
# Impact: MEDIUM | Confidence: MEDIUM

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class ConstantFunctionsAsmDetector(SolidityParserListener):
    """
    Detects view/pure functions that contain assembly code.
    
    Vulnerability: Prior to Solidity 0.5, constant/pure/view was not enforced.
    Starting from 0.5, these functions use STATICCALL which reverts on state modification.
    Functions with assembly might modify state, causing issues when called from 0.5+ contracts.
    
    Example (Problematic):
        function get() public view returns(uint) {
            assembly {
                sstore(0, 1)  // Modifies state but declared as view
            }
            return 1;
        }
    
    Recommendation: Ensure view/pure functions with assembly don't modify state,
    or remove the view/pure modifier if state modification is intended.
    """
    
    def __init__(self):
        self.violations = []
        self.in_function = False
        self.function_name = None
        self.function_modifier = None  # view, pure, or None
        self.function_line = None
        self.contains_assembly = False
    
    def enterFunctionDefinition(self, ctx):
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.function_line = ctx.start.line
        self.function_modifier = None
        self.contains_assembly = False
        
        # Check for view or pure modifiers
        for modifier in ctx.stateMutability():
            modifier_text = modifier.getText()
            if modifier_text in ["view", "pure"]:
                self.function_modifier = modifier_text
                break
    
    def exitFunctionDefinition(self, ctx):
        # Report if function is view/pure and contains assembly
        if self.function_modifier and self.contains_assembly:
            self.violations.append(
                f"⚠️ [S-ATR-001] Function '{self.function_name}' at line {self.function_line} "
                f"is declared '{self.function_modifier}' but contains assembly code. "
                f"Ensure assembly code doesn't modify state, as this can cause issues "
                f"when called from Solidity 0.5+ contracts."
            )
        
        self.in_function = False
        self.function_name = None
        self.function_modifier = None
        self.contains_assembly = False
    
    def enterAssemblyStatement(self, ctx):
        if self.in_function:
            self.contains_assembly = True
    
    def get_violations(self):
        return self.violations
