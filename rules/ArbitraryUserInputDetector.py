from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class ArbitraryUserInputDetector(SolidityParserListener):
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None
        self.function_start_line = None
        self.function_params = set()
        self.has_low_level_call = False
        self.has_arbitrary_input = False
        self.function_has_body = False
        self.has_validation = False

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"

    def exitContractDefinition(self, ctx):
        self.current_contract = None

    def enterFunctionDefinition(self, ctx):
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.function_start_line = ctx.start.line
        self.function_params = set()
        self.has_low_level_call = False
        self.has_arbitrary_input = False
        self.function_has_body = False
        self.has_validation = False
        
        # Extract function parameters
        self._extract_function_parameters(ctx)

    def _extract_function_parameters(self, ctx):
        try:
            if hasattr(ctx, 'arguments') and ctx.arguments:
                param_list = ctx.arguments
                if hasattr(param_list, 'parameterDeclaration'):
                    params = param_list.parameterDeclaration()
                    if params:
                        for param in params:
                            if hasattr(param, 'identifier') and param.identifier():
                                param_name = param.identifier().getText()
                                self.function_params.add(param_name)
                                
                                # Check if parameter is arbitrary user input
                                if self._is_arbitrary_input_param(param):
                                    self.has_arbitrary_input = True
        except Exception:
            pass

    def _is_arbitrary_input_param(self, param):
        """Check if parameter represents arbitrary user input"""
        try:
            if hasattr(param, 'typeName'):
                type_text = param.typeName().getText().lower()
                # Check for types that commonly represent arbitrary data
                # Exclude bytes4 which is often used for function selectors
                arbitrary_types = [
                    'bytes', 'bytes32', 'string',
                    'address', 'uint', 'int'
                ]
                # Explicitly exclude bytes4
                if 'bytes4' in type_text:
                    return False
                return any(arb_type in type_text for arb_type in arbitrary_types)
        except Exception:
            pass
        return False

    def exitFunctionDefinition(self, ctx):
        # Check for security risk: arbitrary input + low-level call without validation
        if (self.has_arbitrary_input and 
            self.has_low_level_call and 
            self.function_has_body and
            not self.has_validation and
            not self._is_constructor(ctx)):
            
            self.violations.append(
                f"❌ [SOL-Basics-Function-6] Security risk in function '{self.function_name}' of contract '{self.current_contract}' at line {self.function_start_line}: Function accepts arbitrary user input and makes low-level calls without proper validation."
            )

        self.in_function = False
        self.function_name = None
        self.function_params = set()
        self.has_low_level_call = False
        self.has_arbitrary_input = False
        self.function_has_body = False
        self.has_validation = False

    def _is_constructor(self, ctx):
        try:
            func_name = ctx.identifier().getText() if ctx.identifier() else ""
            if func_name == "constructor":
                return True
            if func_name == self.current_contract:
                return True
        except Exception:
            pass
        return False

    def enterBlock(self, ctx):
        if self.in_function:
            self.function_has_body = True

    def enterStatement(self, ctx):
        if not self.in_function:
            return
        self._check_statement(ctx.getText())

    def enterExpressionStatement(self, ctx):
        if not self.in_function:
            return
        self._check_statement(ctx.getText())

    def _check_statement(self, text):
        """Check if the text contains low-level calls or validation"""
        # Check for low-level calls
        low_level_call_patterns = [
            ".call(", ".delegatecall(", ".staticcall(",
            "call(", "delegatecall(", "staticcall(",
        ]
        
        if any(pattern in text for pattern in low_level_call_patterns):
            self.has_low_level_call = True

        # Check for validation (but not just call success checks)
        validation_patterns = [
            "require(", "assert(", "revert(",
            "if(", "else if(",
        ]
        
        if any(pattern in text for pattern in validation_patterns):
            # Don't count require(success) as validation for arbitrary input
            if not ("require(success" in text or "require(success," in text):
                self.has_validation = True

    def get_violations(self):
        return self.violations