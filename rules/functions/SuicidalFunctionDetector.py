"""
Detector for unprotected selfdestruct/suicide functions.

This detector identifies public/external functions that call selfdestruct
without proper access control, allowing anyone to destroy the contract.
"""

from typing import List, Set
from antlr4 import ParserRuleContext
from parser.SolidityParser import SolidityParser
from rules.BaseDetector import BaseDetector, DetectorResult, Severity


class SuicidalFunctionDetector(BaseDetector):
    """
    Detects unprotected functions that call selfdestruct/suicide.
    
    A suicidal function is a public/external function that:
    1. Calls selfdestruct or suicide
    2. Has no access control modifiers (onlyOwner, etc.)
    3. Has no require/assert checks for msg.sender
    """

    def __init__(self):
        super().__init__(
            name="Suicidal Function",
            code="S-FNC-005",
            severity=Severity.CRITICAL,
            description="Unprotected function allows anyone to destroy the contract",
            recommendation="Add access control to functions calling selfdestruct. Use modifiers like onlyOwner or require statements to restrict access."
        )
        self.current_contract = None
        self.current_function = None
        self.function_modifiers: Set[str] = set()
        self.has_msg_sender_check = False
        self.calls_selfdestruct = False

    def enterContractDefinition(self, ctx: SolidityParser.ContractDefinitionContext):
        """Track current contract."""
        if ctx.identifier():
            self.current_contract = ctx.identifier().getText()

    def exitContractDefinition(self, ctx: SolidityParser.ContractDefinitionContext):
        """Reset contract tracking."""
        self.current_contract = None

    def enterFunctionDefinition(self, ctx: SolidityParser.FunctionDefinitionContext):
        """Track function and analyze for suicidal patterns."""
        self.current_function = None
        self.function_modifiers = set()
        self.has_msg_sender_check = False
        self.calls_selfdestruct = False

        # Get function name
        if ctx.functionDescriptor():
            if ctx.functionDescriptor().identifier():
                self.current_function = ctx.functionDescriptor().identifier().getText()
            elif ctx.functionDescriptor().getText() in ['constructor', 'fallback', 'receive']:
                self.current_function = ctx.functionDescriptor().getText()

        # Skip constructors
        if self.current_function == 'constructor':
            return

        # Check visibility
        visibility = self._get_visibility(ctx)
        if visibility not in ['public', 'external']:
            return

        # Collect modifiers
        if ctx.modifierList():
            for modifier_invocation in ctx.modifierList().getTypedRuleContexts(
                SolidityParser.ModifierInvocationContext
            ):
                if modifier_invocation.identifier():
                    modifier_name = modifier_invocation.identifier().getText()
                    self.function_modifiers.add(modifier_name)

    def exitFunctionDefinition(self, ctx: SolidityParser.FunctionDefinitionContext):
        """Check if function is suicidal at function exit."""
        if not self.current_function or self.current_function == 'constructor':
            return

        # Get visibility
        visibility = self._get_visibility(ctx)
        if visibility not in ['public', 'external']:
            return

        # Check if function calls selfdestruct
        if not self.calls_selfdestruct:
            return

        # Check if function is protected
        if self._is_protected():
            return

        # Function is suicidal - report it
        line = ctx.start.line if ctx.start else 0
        
        function_sig = self._get_function_signature(ctx)
        
        self.add_result(DetectorResult(
            severity=self.severity,
            line=line,
            code=self.code,
            message=f"Function '{self.current_function}' allows anyone to destroy the contract",
            details=(
                f"The {visibility} function '{function_sig}' calls selfdestruct "
                f"without proper access control. Any user can call this function and "
                f"destroy the contract, leading to loss of funds and functionality."
            ),
            recommendation=self.recommendation,
            contract=self.current_contract,
            function=self.current_function
        ))

    def enterFunctionCall(self, ctx: SolidityParser.FunctionCallContext):
        """Detect selfdestruct/suicide calls."""
        if not self.current_function:
            return

        # Get the function being called
        function_name = self._get_function_call_name(ctx)
        
        if function_name in ['selfdestruct', 'suicide']:
            self.calls_selfdestruct = True

    def enterStatement(self, ctx: SolidityParser.StatementContext):
        """Check for msg.sender access control in require/assert statements."""
        if not self.current_function:
            return

        # Check for require/assert with msg.sender
        if ctx.getChildCount() > 0:
            text = ctx.getText()
            if ('require' in text or 'assert' in text) and 'msg.sender' in text:
                self.has_msg_sender_check = True

    def _is_protected(self) -> bool:
        """
        Check if function has access control protection.
        
        Returns:
            True if function has protection, False otherwise
        """
        # Common access control modifiers
        access_control_modifiers = {
            'onlyOwner', 'onlyAdmin', 'onlyAuthorized', 'onlyGovernance',
            'onlyController', 'onlyMinter', 'onlyRole', 'authorized',
            'isOwner', 'isAdmin', 'requiresAuth', 'onlyGovernor'
        }
        
        # Check if function has access control modifier
        if self.function_modifiers & access_control_modifiers:
            return True
        
        # Check if function has msg.sender check
        if self.has_msg_sender_check:
            return True
        
        return False

    def _get_visibility(self, ctx: SolidityParser.FunctionDefinitionContext) -> str:
        """Extract function visibility."""
        if ctx.modifierList():
            for child in ctx.modifierList().children or []:
                text = child.getText()
                if text in ['public', 'external', 'internal', 'private']:
                    return text
        return 'public'  # Default visibility

    def _get_function_signature(self, ctx: SolidityParser.FunctionDefinitionContext) -> str:
        """Build function signature with parameters."""
        if not self.current_function:
            return "unknown"
        
        params = []
        if ctx.parameterList():
            for param in ctx.parameterList().getTypedRuleContexts(SolidityParser.ParameterContext):
                if param.typeName():
                    param_type = param.typeName().getText()
                    param_name = ""
                    if param.identifier():
                        param_name = param.identifier().getText()
                    params.append(f"{param_type} {param_name}".strip())
        
        return f"{self.current_function}({', '.join(params)})"

    def _get_function_call_name(self, ctx: SolidityParser.FunctionCallContext) -> str:
        """Extract the name of the function being called."""
        if ctx.expression():
            expr = ctx.expression()
            
            # Direct function call
            if expr.identifier():
                return expr.identifier().getText()
            
            # Get the full expression text and extract function name
            expr_text = expr.getText()
            
            # Handle member access (e.g., address.selfdestruct)
            if '.' in expr_text:
                parts = expr_text.split('.')
                return parts[-1]
            
            return expr_text
        
        return ""
