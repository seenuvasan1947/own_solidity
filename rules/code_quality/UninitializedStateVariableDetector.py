from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class UninitializedStateVariableDetector(SolidityParserListener):
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.constructor_variables = set()
        self.state_variables = {}  # {name: initialized}

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.constructor_variables.clear()
        self.state_variables.clear()

    def exitContractDefinition(self, ctx):
        # Check for uninitialized state variables
        for var_name, initialized in self.state_variables.items():
            if not initialized and var_name not in self.constructor_variables:
                line = ctx.start.line
                self.violations.append(f"❌ Uninitialized state variable '{var_name}' in contract '{self.current_contract}' at line {line}")
        self.current_contract = None

    def enterStateVariableDeclaration(self, ctx):
        # Get variable name and check if it has an initial value
        var_name = ctx.name.getText()
        has_initial_value = ctx.initialValue is not None
        
        # Check if variable is constant or immutable
        is_constant = any(mod.getText() == 'constant' for mod in ctx.children if hasattr(mod, 'getText'))
        is_immutable = any(mod.getText() == 'immutable' for mod in ctx.children if hasattr(mod, 'getText'))
        
        # Only track non-constant, non-immutable state variables
        if not is_constant and not is_immutable:
            self.state_variables[var_name] = has_initial_value

    def enterConstructorDefinition(self, ctx):
        # Track variables initialized in constructor
        if ctx.body:
            for node in ctx.body.children:
                if isinstance(node, SolidityParser.ExpressionStatementContext):
                    expr = node.expression()
                    if isinstance(expr, SolidityParser.AssignmentContext):
                        left_expr = expr.expression(0)
                        if isinstance(left_expr, SolidityParser.PrimaryExpressionContext):
                            var_name = left_expr.getText()
                            if var_name in self.state_variables:
                                self.constructor_variables.add(var_name)

    def get_violations(self):
        return self.violations
