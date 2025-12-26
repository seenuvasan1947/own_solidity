"""
Detector for out-of-order retryable transactions on Arbitrum L2.

This detector identifies functions that create multiple retryable tickets
which could execute out of order, leading to unexpected behavior.
"""

from typing import List, Set, Dict
from antlr4 import ParserRuleContext
from parser.SolidityParser import SolidityParser
from rules.BaseDetector import BaseDetector, DetectorResult, Severity


class OutOfOrderRetryableDetector(BaseDetector):
    """
    Detects out-of-order retryable transaction risks on Arbitrum.
    
    Identifies functions that create multiple retryable tickets which may
    execute in a different order than intended, causing logic errors.
    
    Retryable ticket functions:
    - createRetryableTicket
    - outboundTransferCustomRefund
    - unsafeCreateRetryableTicket
    """

    def __init__(self):
        super().__init__(
            name="Out-of-Order Retryable Transactions",
            code="S-L2-002",
            severity=Severity.MEDIUM,
            description="Multiple retryable tickets in same function may execute out of order",
            recommendation="Do not rely on the order or successful execution of retryable tickets. Consider using a single retryable ticket or implementing proper sequencing logic."
        )
        self.current_contract = None
        self.current_function = None
        self.retryable_calls: Dict[str, List[dict]] = {}  # {function_name: [{line, call_name}]}

    def enterContractDefinition(self, ctx: SolidityParser.ContractDefinitionContext):
        """Track current contract."""
        if ctx.identifier():
            self.current_contract = ctx.identifier().getText()

    def exitContractDefinition(self, ctx: SolidityParser.ContractDefinitionContext):
        """Reset contract tracking."""
        self.current_contract = None

    def enterFunctionDefinition(self, ctx: SolidityParser.FunctionDefinitionContext):
        """Track current function."""
        self.current_function = None
        
        if ctx.functionDescriptor():
            if ctx.functionDescriptor().identifier():
                self.current_function = ctx.functionDescriptor().identifier().getText()
            elif ctx.functionDescriptor().getText() in ['constructor', 'fallback', 'receive']:
                self.current_function = ctx.functionDescriptor().getText()

        if self.current_function:
            self.retryable_calls[self.current_function] = []

    def exitFunctionDefinition(self, ctx: SolidityParser.FunctionDefinitionContext):
        """Check for multiple retryable tickets at function exit."""
        if not self.current_function:
            return

        retryable_list = self.retryable_calls.get(self.current_function, [])
        
        # Report if multiple retryable tickets found
        if len(retryable_list) > 1:
            line = ctx.start.line if ctx.start else 0
            
            call_details = "\n".join([
                f"  - Line {call['line']}: {call['call_name']}"
                for call in retryable_list
            ])
            
            self.add_result(DetectorResult(
                severity=self.severity,
                line=line,
                code=self.code,
                message=f"Function '{self.current_function}' creates {len(retryable_list)} retryable tickets that may execute out of order",
                details=(
                    f"The function '{self.current_function}' creates multiple retryable tickets:\n"
                    f"{call_details}\n\n"
                    f"Retryable tickets on Arbitrum can fail or execute in a different order than "
                    f"created. If the logic depends on sequential execution (e.g., claim_rewards "
                    f"before unstake), users may lose funds or experience unexpected behavior if "
                    f"tickets execute out of order or some fail."
                ),
                recommendation=self.recommendation,
                contract=self.current_contract,
                function=self.current_function
            ))

        self.current_function = None

    def enterFunctionCall(self, ctx: SolidityParser.FunctionCallContext):
        """Detect retryable ticket creation calls."""
        if not self.current_function:
            return

        function_name = self._get_function_call_name(ctx)
        
        # Check if it's a retryable ticket function
        retryable_functions = {
            'createRetryableTicket',
            'outboundTransferCustomRefund',
            'unsafeCreateRetryableTicket'
        }
        
        if function_name in retryable_functions:
            line = ctx.start.line if ctx.start else 0
            self.retryable_calls[self.current_function].append({
                'line': line,
                'call_name': function_name
            })

    def _get_function_call_name(self, ctx: SolidityParser.FunctionCallContext) -> str:
        """Extract the name of the function being called."""
        if ctx.expression():
            expr = ctx.expression()
            
            # Direct function call
            if expr.identifier():
                return expr.identifier().getText()
            
            # Get the full expression text
            expr_text = expr.getText()
            
            # Handle member access (e.g., inbox.createRetryableTicket)
            if '.' in expr_text:
                parts = expr_text.split('.')
                return parts[-1]
            
            return expr_text
        
        return ""
