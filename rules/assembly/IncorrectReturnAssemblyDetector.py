# S-ASM-001: Incorrect Return in Assembly
# Detects incorrect use of return() in assembly blocks that can halt execution unexpectedly
# Based on Slither's incorrect_return detector
# Impact: HIGH | Confidence: MEDIUM

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class IncorrectReturnAssemblyDetector(SolidityParserListener):
    """
    Detects incorrect use of return() in assembly blocks.
    
    Vulnerability: Using return(a,b) in assembly within an internal function
    can halt execution unexpectedly instead of returning values properly.
    
    Example:
        function f() internal returns (uint a, uint b) {
            assembly {
                return(5, 6)  // BAD: Halts execution
            }
        }
    
    Recommendation: Use 'leave' statement instead of 'return' in assembly.
    """
    
    def __init__(self):
        self.violations = []
        self.in_assembly = False
        self.in_function = False
        self.function_name = None
        self.function_visibility = None
        self.function_has_returns = False
        self.function_line = None
        self.assembly_start_line = None
    
    def enterFunctionDefinition(self, ctx):
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.function_line = ctx.start.line
        self.function_has_returns = False
        self.function_visibility = None
        
        # Check visibility
        for vis in ctx.visibility():
            vis_text = vis.getText()
            if vis_text in ["public", "external", "internal", "private"]:
                self.function_visibility = vis_text
                break
        
        # Check if function has return parameters
        if ctx.returnParameters():
            self.function_has_returns = True
    
    def exitFunctionDefinition(self, ctx):
        self.in_function = False
        self.function_name = None
        self.function_visibility = None
        self.function_has_returns = False
    
    def enterAssemblyStatement(self, ctx):
        if self.in_function:
            self.in_assembly = True
            self.assembly_start_line = ctx.start.line
    
    def exitAssemblyStatement(self, ctx):
        self.in_assembly = False
        self.assembly_start_line = None
    
    def enterYulFunctionCall(self, ctx):
        if not self.in_assembly or not self.in_function:
            return
        
        # Check if this is a return call in assembly
        func_name = ctx.getText()
        
        if func_name.startswith("return("):
            line = ctx.start.line
            
            # This is problematic especially for internal/private functions
            if self.function_visibility in ["internal", "private"] and self.function_has_returns:
                self.violations.append(
                    f"❌ [S-ASM-001] Incorrect return in assembly at line {line}: "
                    f"Function '{self.function_name}' uses return() in assembly which can halt execution unexpectedly. "
                    f"Use 'leave' statement instead."
                )
            elif self.function_has_returns:
                self.violations.append(
                    f"⚠️ [S-ASM-001] Potentially incorrect return in assembly at line {line}: "
                    f"Function '{self.function_name}' uses return() in assembly. "
                    f"Verify this is intentional or use 'leave' statement."
                )
    
    def enterStatement(self, ctx):
        if not self.in_assembly or not self.in_function:
            return
        
        # Also check for return in regular statements within assembly
        text = ctx.getText().lower()
        if "return(" in text:
            line = ctx.start.line
            
            if self.function_visibility in ["internal", "private"] and self.function_has_returns:
                self.violations.append(
                    f"❌ [S-ASM-001] Incorrect return in assembly at line {line}: "
                    f"Function '{self.function_name}' uses return() in assembly which can halt execution unexpectedly. "
                    f"Use 'leave' statement instead."
                )
    
    def get_violations(self):
        return self.violations
