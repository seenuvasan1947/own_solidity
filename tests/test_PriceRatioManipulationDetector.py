import unittest
from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from rules.PriceRatioManipulationDetector import PriceRatioManipulationDetector  # import your rule

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

class TestPriceRatioManipulationDetector(unittest.TestCase):
    def test_detects_price_manipulation(self):
        violations = run_rule_on_file("test_contracts/PriceRatioManipulationDetector_bad.sol", PriceRatioManipulationDetector)
        self.assertTrue(any("Price derived directly from DEX liquidity pool" in v for v in violations), f"Violations: {violations}")

    def test_ignores_safe_contract(self):
        violations = run_rule_on_file("test_contracts/PriceRatioManipulationDetector_good.sol", PriceRatioManipulationDetector)
        self.assertEqual(len(violations), 0, f"Expected 0 violations, got: {violations}")