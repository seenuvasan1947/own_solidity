# S-ASM-002: Incorrect Shift Parameter Order
# Detects reversed parameters in shift operations (shl/shr) in assembly
# Based on Slither's shift_parameter_mixup detector
# Impact: HIGH | Confidence: HIGH

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class ShiftParameterMixupDetector(SolidityParserListener):
    """
    Detects incorrect parameter order in shift operations within assembly blocks.
    
    Vulnerability: In assembly, shift operations like shl(x, y) and shr(x, y)
    shift y by x bits. If a constant is used as the first parameter and a
    variable as the second, the parameters are likely reversed.
    
    Correct: shr(8, a)  // Shift 'a' right by 8 bits
    Incorrect: shr(a, 8)  // Shift constant 8 by 'a' bits (likely wrong)
    
    Example:
        assembly {
            a := shr(a, 8)  // BAD: Shifts 8 by 'a' bits
            a := shr(8, a)  // GOOD: Shifts 'a' by 8 bits
        }
    
    Recommendation: Swap the order of parameters in shift operations.
    """
    
    def __init__(self):
        self.violations = []
        self.in_assembly = False
        self.in_function = False
        self.function_name = None
        self.assembly_depth = 0
    
    def enterFunctionDefinition(self, ctx):
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
    
    def exitFunctionDefinition(self, ctx):
        self.in_function = False
        self.function_name = None
    
    def enterAssemblyStatement(self, ctx):
        self.in_assembly = True
        self.assembly_depth += 1
    
    def exitAssemblyStatement(self, ctx):
        self.assembly_depth -= 1
        if self.assembly_depth == 0:
            self.in_assembly = False
    
    def enterYulFunctionCall(self, ctx):
        if not self.in_assembly:
            return
        
        self._check_shift_operation(ctx)
    
    def enterYulAssignment(self, ctx):
        if not self.in_assembly:
            return
        
        # Check the right side of assignment for shift operations
        text = ctx.getText()
        self._analyze_shift_in_text(text, ctx.start.line)
    
    def enterYulStatement(self, ctx):
        if not self.in_assembly:
            return
        
        text = ctx.getText()
        self._analyze_shift_in_text(text, ctx.start.line)
    
    def _check_shift_operation(self, ctx):
        """Check if a function call is a shift operation with incorrect parameters"""
        text = ctx.getText()
        line = ctx.start.line
        
        # Check for shift operations: shl, shr, sar
        shift_pattern = r'(shl|shr|sar)\s*\(\s*([^,]+)\s*,\s*([^)]+)\s*\)'
        matches = re.finditer(shift_pattern, text, re.IGNORECASE)
        
        for match in matches:
            operation = match.group(1)
            first_param = match.group(2).strip()
            second_param = match.group(3).strip()
            
            # Check if first parameter looks like a variable and second like a constant
            if self._is_likely_variable(first_param) and self._is_likely_constant(second_param):
                self.violations.append(
                    f"❌ [S-ASM-002] Incorrect shift parameter order at line {line}: "
                    f"{operation}({first_param}, {second_param}) - "
                    f"Parameters appear reversed. Should be {operation}({second_param}, {first_param}). "
                    f"Shift operations shift the second parameter by the first parameter bits."
                )
    
    def _analyze_shift_in_text(self, text, line):
        """Analyze text for shift operations with incorrect parameter order"""
        # Pattern to match shift operations
        shift_pattern = r'(shl|shr|sar)\s*\(\s*([^,]+)\s*,\s*([^)]+)\s*\)'
        matches = re.finditer(shift_pattern, text, re.IGNORECASE)
        
        for match in matches:
            operation = match.group(1)
            first_param = match.group(2).strip()
            second_param = match.group(3).strip()
            
            # Check if first parameter looks like a variable and second like a constant
            if self._is_likely_variable(first_param) and self._is_likely_constant(second_param):
                self.violations.append(
                    f"❌ [S-ASM-002] Incorrect shift parameter order at line {line}: "
                    f"{operation}({first_param}, {second_param}) - "
                    f"Parameters appear reversed. Should be {operation}({second_param}, {first_param}). "
                    f"Shift operations shift the second parameter by the first parameter bits."
                )
    
    def _is_likely_constant(self, param):
        """Check if parameter looks like a constant (number or hex)"""
        param = param.strip()
        # Check for decimal numbers
        if param.isdigit():
            return True
        # Check for hex numbers
        if param.startswith('0x') or param.startswith('0X'):
            return True
        # Check for common constant patterns
        if re.match(r'^[0-9]+$', param):
            return True
        return False
    
    def _is_likely_variable(self, param):
        """Check if parameter looks like a variable (identifier)"""
        param = param.strip()
        # Variable names typically start with letter or underscore
        if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', param):
            return True
        return False
    
    def get_violations(self):
        return self.violations
