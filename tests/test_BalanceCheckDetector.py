import unittest
from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from rules.BalanceCheckDetector import BalanceCheckDetector  # import your rule

def run_rule_on_file(filepath, rule_class):
    input_stream = FileStream(filepath)
    lexer = SolidityLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = SolidityParser(stream)
    tree = parser.sourceUnit()

    rule_instance = rule_class()
    walker = ParseTreeWalker()
    walker.walk(rule_instance, tree)

    return rule_instance.get_violations()

class TestBalanceCheckDetector(unittest.TestCase):
    
    def test_detects_balance_check(self):
        violations = run_rule_on_file("test_contracts/BalanceCheckDetector_bad.sol", BalanceCheckDetector)
        print(violations)
        self.assertTrue(any("Potential Donation Attack" in v for v in violations))

    def test_ignores_safe_contract(self):
        violations = run_rule_on_file("test_contracts/BalanceCheckDetector_good.sol", BalanceCheckDetector)
        self.assertEqual(len(violations), 0, f"Expected 0 violations, got: {violations}")

if __name__ == "__main__":
    unittest.main()
    