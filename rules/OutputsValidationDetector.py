from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class OutputsValidationDetector(SolidityParserListener):
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None
        self.return_vars = set()
        self.validated_returns = set()
        self.function_start_line = None
        self.function_has_body = False

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"

    def exitContractDefinition(self, ctx):
        self.current_contract = None

    def enterFunctionDefinition(self, ctx):
        self.in_function = True
        self.validated_returns = set()
        self.return_vars = set()
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.function_start_line = ctx.start.line
        self.function_has_body = False
        self._extract_return_variables(ctx)

    def _extract_return_variables(self, ctx):
        try:
            if hasattr(ctx, 'returnParameters') and ctx.returnParameters:
                param_list = ctx.returnParameters
                if hasattr(param_list, 'parameterDeclaration'):
                    params = param_list.parameterDeclaration()
                    if params:
                        for param in params:
                            if hasattr(param, 'identifier') and param.identifier():
                                var_name = param.identifier().getText()
                                self.return_vars.add(var_name)
            # fallback: parse from text
            if not self.return_vars:
                func_text = ctx.getText()
                import re
                # match returns (...) in function signature
                m = re.search(r'returns\s*\(([^)]*)\)', func_text)
                if m:
                    params_str = m.group(1)
                    for part in params_str.split(','):
                        tokens = part.strip().split()
                        if len(tokens) >= 2:
                            var_name = tokens[-1]
                            self.return_vars.add(var_name)
        except Exception:
            pass

    def exitFunctionDefinition(self, ctx):
        if self.return_vars and self.function_has_body:
            missing_validation = self.return_vars - self.validated_returns
            if missing_validation:
                params_str = ", ".join(missing_validation)
                self.violations.append(
                    f"❌ [SOL-Basics-Function-2] Missing output validation in function '{self.function_name}' of contract '{self.current_contract}' at line {self.function_start_line}: Return variables [{params_str}] are not validated."
                )
        self.in_function = False
        self.function_name = None
        self.return_vars = set()
        self.validated_returns = set()
        self.function_has_body = False

    def enterBlock(self, ctx):
        if self.in_function:
            self.function_has_body = True

    def enterStatement(self, ctx):
        if not self.in_function:
            return
        self._check_for_output_validation(ctx.getText())

    def enterExpressionStatement(self, ctx):
        if not self.in_function:
            return
        self._check_for_output_validation(ctx.getText())

    def _check_for_output_validation(self, text):
        validation_patterns = ["require(", "assert(", "if("]
        has_validation = any(pattern in text for pattern in validation_patterns)
        if has_validation:
            for var in self.return_vars:
                if self._is_var_validated(var, text):
                    self.validated_returns.add(var)

    def _is_var_validated(self, var, text):
        import re
        pattern = r'\b' + re.escape(var) + r'\b'
        return bool(re.search(pattern, text))

    def get_violations(self):
        return self.violations 