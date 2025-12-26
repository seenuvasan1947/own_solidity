from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class InputsValidationDetector(SolidityParserListener):
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None
        self.function_params = set()
        self.checked_params = set()
        self.function_start_line = None
        self.function_has_body = False

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"

    def exitContractDefinition(self, ctx):
        self.current_contract = None

    def enterFunctionDefinition(self, ctx):
        self.in_function = True
        self.checked_params = set()
        self.function_params = set()
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.function_start_line = ctx.start.line
        self.function_has_body = False

        # Extract function parameters using a more robust approach
        self._extract_function_parameters(ctx)

    def _extract_function_parameters(self, ctx):
        """Extract function parameters from the context"""
        try:
            # Method 1: Try to get arguments from context (this is the correct way)
            if hasattr(ctx, 'arguments') and ctx.arguments:
                param_list = ctx.arguments
                if hasattr(param_list, 'parameterDeclaration'):
                    params = param_list.parameterDeclaration()
                    if params:
                        for param in params:
                            if hasattr(param, 'identifier') and param.identifier():
                                param_name = param.identifier().getText()
                                self.function_params.add(param_name)
                                print(f"Found parameter: {param_name}")

            # Method 2: Parse function text directly as fallback
            if not self.function_params:
                func_text = ctx.getText()
                self._parse_parameters_from_text(func_text)

        except Exception as e:
            print(f"Error extracting parameters: {e}")
            # Fallback: try to parse from raw text
            try:
                func_text = ctx.getText()
                self._parse_parameters_from_text(func_text)
            except Exception as e2:
                print(f"Fallback parsing also failed: {e2}")

    def _parse_parameters_from_text(self, func_text):
        """Parse parameters from function text using regex"""
        import re
        
        # Find function signature pattern: function_name(type param1, type param2, ...)
        # This regex looks for parameter patterns inside parentheses
        pattern = r'\([^)]*\)'
        match = re.search(pattern, func_text)
        
        if match:
            params_str = match.group(0)[1:-1]  # Remove parentheses
            if params_str.strip():
                # Split by comma and extract parameter names
                param_parts = [p.strip() for p in params_str.split(',')]
                for part in param_parts:
                    # Each part should be like "uint256 value" or "address to"
                    tokens = part.split()
                    if len(tokens) >= 2:
                        param_name = tokens[-1]  # Last token is usually the parameter name
                        # Filter out keywords that aren't parameter names
                        if param_name not in ['public', 'private', 'external', 'internal', 'pure', 'view', 'payable', 'memory', 'storage', 'calldata']:
                            self.function_params.add(param_name)
                            print(f"Found parameter from text: {param_name}")

    def exitFunctionDefinition(self, ctx):
        # Only check functions that have parameters and a body
        print(f"Function {self.function_name} has params: {self.function_params}, has body: {self.function_has_body}")
        if self.function_params and self.function_has_body:
            missing_validation = self.function_params - self.checked_params
            if missing_validation:
                params_str = ", ".join(missing_validation)
                self.violations.append(
                    f"❌ Missing input validation in function '{self.function_name}' of contract '{self.current_contract}' at line {self.function_start_line}: Parameters [{params_str}] are not validated."
                )

        self.in_function = False
        self.function_name = None
        self.function_params = set()
        self.checked_params = set()
        self.function_has_body = False

    def enterBlock(self, ctx):
        # If we're in a function and see a block, the function has a body
        if self.in_function:
            self.function_has_body = True

    def enterStatement(self, ctx):
        if not self.in_function:
            return
        
        self._check_for_validation(ctx.getText())

    def enterExpressionStatement(self, ctx):
        if not self.in_function:
            return
        
        self._check_for_validation(ctx.getText())

    def _check_for_validation(self, text):
        """Check if the text contains validation patterns and mark validated parameters"""
        # Common validation patterns
        validation_patterns = [
            "require(",
            "assert(",
            "revert(",
            "if("
        ]
        
        # Check if this statement contains validation
        has_validation = any(pattern in text for pattern in validation_patterns)
        
        if has_validation:
            # Check which parameters are mentioned in this validation
            for param in self.function_params:
                if self._is_parameter_validated(param, text):
                    self.checked_params.add(param)

    def _is_parameter_validated(self, param, text):
        """Check if a parameter is mentioned in a validation context"""
        import re
        
        # Use word boundaries to ensure we match the exact parameter name
        pattern = r'\b' + re.escape(param) + r'\b'
        return bool(re.search(pattern, text))

    def get_violations(self):
        return self.violations
