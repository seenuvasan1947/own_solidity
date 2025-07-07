import unittest
from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from rules.PriceManipulationDetector import PriceManipulationDetector

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

class TestCommitRevealDetector(unittest.TestCase):
    def test_detects_vulnerability(self):
        violations = run_rule_on_file("test_contracts/PriceManipulationDetector_bad.sol", PriceManipulationDetector)
        self.assertTrue(len(violations) > 0, "Vulnerability should be detected")

    def test_ignores_safe_contract(self):
        violations = run_rule_on_file("test_contracts/PriceManipulationDetector_good.sol", PriceManipulationDetector)
        self.assertEqual(len(violations), 0, f"Expected 0 violations, got: {violations}")

if __name__ == "__main__":
    unittest.main()