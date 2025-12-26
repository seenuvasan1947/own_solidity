# S-ASM-003: Return Instead of Leave in Assembly
# Detects use of return() instead of leave in assembly for functions with return values
# Based on Slither's return_instead_of_leave detector
# Impact: HIGH | Confidence: MEDIUM

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class ReturnInsteadOfLeaveDetector(SolidityParserListener):
    """
    Detects incorrect use of return() instead of leave in assembly blocks.
    
    Vulnerability: When a function has return parameters and uses assembly,
    using return() instead of leave will halt execution and return raw bytes
    instead of properly setting the return variables.
    
    Specifically checks for:
    - Functions with return parameters (especially 2 return values)
    - Internal or private visibility
    - Contains assembly block
    - Uses return() in assembly
    
    Example (BAD):
        function f() internal returns (uint a, uint b) {
            assembly {
                return(5, 6)  // BAD: Halts execution, returns raw bytes
            }
        }
    
    Example (GOOD):
        function f() internal returns (uint a, uint b) {
            assembly {
                a := 5
                b := 6
                leave  // GOOD: Properly exits assembly and returns values
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
        self.return_param_count = 0
        self.function_line = None
    
    def enterFunctionDefinition(self, ctx):
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.function_line = ctx.start.line
        self.return_param_count = 0
        self.function_visibility = None
        
        # Check visibility
        for vis in ctx.visibility():
            vis_text = vis.getText()
            if vis_text in ["public", "external", "internal", "private"]:
                self.function_visibility = vis_text
                break
        
        # If no explicit visibility, default is internal for functions
        if not self.function_visibility:
            self.function_visibility = "internal"
        
        # Count return parameters
        if ctx.returnParameters():
            return_params = ctx.returnParameters()
            # Try to count parameters in the return list
            param_list = return_params.parameterList()
            if param_list:
                # Count parameter declarations
                i = 0
                while True:
                    param = param_list.parameterDeclaration(i)
                    if param is None:
                        break
                    self.return_param_count += 1
                    i += 1
    
    def exitFunctionDefinition(self, ctx):
        self.in_function = False
        self.function_name = None
        self.function_visibility = None
        self.return_param_count = 0
    
    def enterAssemblyStatement(self, ctx):
        if self.in_function:
            self.in_assembly = True
    
    def exitAssemblyStatement(self, ctx):
        self.in_assembly = False
    
    def enterYulFunctionCall(self, ctx):
        if not self.in_assembly or not self.in_function:
            return
        
        self._check_return_call(ctx)
    
    def enterYulStatement(self, ctx):
        if not self.in_assembly or not self.in_function:
            return
        
        text = ctx.getText()
        line = ctx.start.line
        
        # Check for return calls in assembly
        if "return(" in text.lower():
            self._report_if_problematic(line, text)
    
    def _check_return_call(self, ctx):
        """Check if this is a problematic return call"""
        text = ctx.getText()
        line = ctx.start.line
        
        if text.startswith("return("):
            self._report_if_problematic(line, text)
    
    def _report_if_problematic(self, line, text):
        """Report violation if conditions are met"""
        # Only flag if:
        # 1. Function has return parameters (especially 2)
        # 2. Function is internal or private
        # 3. Using return() in assembly
        
        if self.return_param_count > 0 and self.function_visibility in ["internal", "private"]:
            # Higher confidence if exactly 2 return parameters (common pattern)
            if self.return_param_count == 2:
                self.violations.append(
                    f"❌ [S-ASM-003] Return instead of leave in assembly at line {line}: "
                    f"Function '{self.function_name}' returns {self.return_param_count} values but uses return() in assembly. "
                    f"This will halt execution and return raw bytes instead of setting return variables. "
                    f"Use 'leave' statement instead."
                )
            else:
                self.violations.append(
                    f"⚠️ [S-ASM-003] Potential return instead of leave in assembly at line {line}: "
                    f"Function '{self.function_name}' returns {self.return_param_count} value(s) but uses return() in assembly. "
                    f"Consider using 'leave' statement instead."
                )
        elif self.return_param_count > 0:
            # Public/external functions with return values - less critical but still worth noting
            self.violations.append(
                f"⚠️ [S-ASM-003] Return in assembly for function with return values at line {line}: "
                f"Function '{self.function_name}' ({self.function_visibility}) returns {self.return_param_count} value(s). "
                f"Verify that return() usage in assembly is intentional."
            )
    
    def get_violations(self):
        return self.violations
