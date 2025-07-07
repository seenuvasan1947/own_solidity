from antlr4 import *
from SolidityParserListener import SolidityParserListener
from SolidityParser import SolidityParser

class BalanceCheckDetector(SolidityParserListener):
    def __init__(self):
        self.violations = []

    def enterExpressionStatement(self, ctx: SolidityParser.FunctionDefinitionContext):
        line = ctx.start.line
        text = ctx.getText().replace(" ", "").lower()

        print(f"[DEBUG] Line {line}: {text}")

        if self._is_direct_balanceof_in_require(text):
            self._report_violation(
                line,
                "❌ Potential Donation Attack at line {}: Detected unsafe use of `balanceOf(address(this))` inside require(). Consider using internal accounting.".format(line)
            )

        elif self._is_raw_balance_check_in_require(text):
            self._report_violation(
                line,
                "❌ Potential Donation Attack at line {}: Detected raw `balance` check. Consider using internal accounting.".format(line)
            )

    def _is_direct_balanceof_in_require(self, text: str) -> bool:
        return "require(" in text and "balanceof(address(this))" in text

    def _is_raw_balance_check_in_require(self, text: str) -> bool:
     return (
         "require(" in text and
         "balance" in text and
         "msg.sender.balance" not in text and
         "balanceof" not in text and
         "internal" not in text  # Exclude internal balances like internalTokenBalance
     )

    def _report_violation(self, line: int, message: str):
        print(f"[DEBUG] Reporting violation at line {line}")
        self.violations.append(message)

    def get_violations(self):
        return self.violations
