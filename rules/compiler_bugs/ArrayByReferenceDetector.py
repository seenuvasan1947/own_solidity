# S-BUG-004: Array By Reference
# Detects passing storage arrays to functions expecting memory arrays
# Based on Slither's array_by_reference detector
# Impact: HIGH | Confidence: HIGH

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class ArrayByReferenceDetector(SolidityParserListener):
    """
    Detects modifying storage arrays by value instead of reference.
    
    Vulnerability: Passing a storage array to a function that expects
    a memory array creates a copy. Modifications to the copy don't
    affect the original storage array.
    
    Example (BAD):
        uint[1] public x;  // storage
        
        function f() public {
            f2(x);  // Passes copy, not reference
        }
        
        function f2(uint[1] arr) internal {  // Takes memory array
            arr[0] = 2;  // Modifies copy, not x
        }
    
    Recommendation: Use explicit 'storage' keyword for array parameters
    that should modify the original array.
    """
    
    def __init__(self):
        self.violations = []
        self.functions = {}  # func_name -> (params_with_location, line)
        self.in_function = False
        self.current_function = None
    
    def enterFunctionDefinition(self, ctx):
        func_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        line = ctx.start.line
        
        # Check parameters for array types without explicit storage location
        params_info = []
        if ctx.parameterList():
            param_list = ctx.parameterList()
            i = 0
            while True:
                param = param_list.parameterDeclaration(i)
                if param is None:
                    break
                
                param_text = param.getText()
                param_name = param.identifier().getText() if param.identifier() else f"param{i}"
                
                # Check if it's an array parameter
                if '[' in param_text and ']' in param_text:
                    # Check for explicit location (storage, memory, calldata)
                    has_storage = 'storage' in param_text
                    has_memory = 'memory' in param_text
                    has_calldata = 'calldata' in param_text
                    
                    params_info.append({
                        'name': param_name,
                        'is_array': True,
                        'has_storage': has_storage,
                        'has_memory': has_memory,
                        'has_calldata': has_calldata,
                        'implicit_memory': not (has_storage or has_memory or has_calldata)
                    })
                
                i += 1
        
        self.functions[func_name] = (params_info, line)
        self.in_function = True
        self.current_function = func_name
    
    def exitFunctionDefinition(self, ctx):
        self.in_function = False
        self.current_function = None
    
    def enterExpressionStatement(self, ctx):
        if not self.in_function:
            return
        
        text = ctx.getText()
        line = ctx.start.line
        
        # Check for function calls with array arguments
        for func_name, (params_info, func_line) in self.functions.items():
            if f"{func_name}(" in text:
                # Check if this function has array parameters without explicit storage
                for param in params_info:
                    if param['is_array'] and param['implicit_memory']:
                        self.violations.append(
                            f"⚠️ [S-BUG-004] Potential array-by-value issue at line {line}: "
                            f"Function '{func_name}' has array parameter '{param['name']}' without "
                            f"explicit location specifier. If passing storage arrays, modifications "
                            f"won't affect the original. Add 'storage', 'memory', or 'calldata' keyword."
                        )
                        break
    
    def get_violations(self):
        return self.violations
