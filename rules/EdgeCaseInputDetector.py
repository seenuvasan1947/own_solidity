from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class EdgeCaseInputDetector(SolidityParserListener):
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None
        self.function_start_line = None
        self.function_params = set()
        self.edge_cases_handled = set()
        self.function_has_body = False

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"

    def exitContractDefinition(self, ctx):
        self.current_contract = None

    def enterFunctionDefinition(self, ctx):
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.function_start_line = ctx.start.line
        self.function_params = set()
        self.edge_cases_handled = set()
        self.function_has_body = False
        
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
        except Exception:
            pass

    def exitFunctionDefinition(self, ctx):
        if self.function_params and self.function_has_body:
            # Check if edge cases are handled for numeric parameters
            # For now, assume all parameters need edge case validation
            missing_edge_cases = []
            
            for param in self.function_params:
                if not self._has_edge_case_validation(param):
                    missing_edge_cases.append(param)
            
            if missing_edge_cases:
                params_str = ", ".join(missing_edge_cases)
                self.violations.append(
                    f"❌ [SOL-Basics-Function-5] Missing edge case validation in function '{self.function_name}' of contract '{self.current_contract}' at line {self.function_start_line}: Parameters [{params_str}] lack validation for edge cases (0, max values)."
                )

        self.in_function = False
        self.function_name = None
        self.function_params = set()
        self.edge_cases_handled = set()
        self.function_has_body = False

    def _has_edge_case_validation(self, param_name):
        """Check if parameter has edge case validation"""
        return param_name in self.edge_cases_handled

    def enterBlock(self, ctx):
        if self.in_function:
            self.function_has_body = True

    def enterStatement(self, ctx):
        if not self.in_function:
            return
        self._check_edge_case_validation(ctx.getText())

    def enterExpressionStatement(self, ctx):
        if not self.in_function:
            return
        self._check_edge_case_validation(ctx.getText())

    def _check_edge_case_validation(self, text):
        """Check if the text contains edge case validation patterns"""
        edge_case_patterns = [
            "require(", "assert(", "revert(",
            "if(", "else if(",
            "> 0", ">= 0", "< 0", "<= 0",
            "!= 0", "== 0",
            "type(uint256).max", "type(int256).max",
            "type(uint256).min", "type(int256).min",
        ]
        
        has_validation = any(pattern in text for pattern in edge_case_patterns)
        
        if has_validation:
            # Check which parameters are mentioned in edge case validation
            for param in self.function_params:
                if self._is_parameter_in_edge_validation(param, text):
                    self.edge_cases_handled.add(param)

    def _is_parameter_in_edge_validation(self, param, text):
        """Check if a parameter is mentioned in edge case validation context"""
        import re
        
        # Use word boundaries to ensure we match the exact parameter name
        pattern = r'\b' + re.escape(param) + r'\b'
        if re.search(pattern, text):
            # Check if it's in a validation context - be more flexible
            validation_contexts = [
                f"{param} >", f"{param} >=", f"{param} <", f"{param} <=",
                f"{param} ==", f"{param} !=",
                f"> {param}", f">= {param}", f"< {param}", f"<= {param}",
                f"== {param}", f"!= {param}",
                # Also check for the parameter being in a require statement
                f"require({param}",
                f"assert({param}",
                f"revert({param}",
            ]
            return any(context in text for context in validation_contexts)
        return False

    def get_violations(self):
        return self.violations 