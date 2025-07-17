import unittest
from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from rules.ArbitraryUserInputDetector import ArbitraryUserInputDetector

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

class TestArbitraryUserInputDetector(unittest.TestCase):
    def test_detects_arbitrary_input_risk(self):
        violations = run_rule_on_file("test_contracts/ArbitraryUserInputDetector_bad.sol", ArbitraryUserInputDetector)
        self.assertTrue(any("arbitrary user input" in v for v in violations))

    def test_passes_safe_contract(self):
        violations = run_rule_on_file("test_contracts/ArbitraryUserInputDetector_good.sol", ArbitraryUserInputDetector)
        self.assertEqual(len(violations), 0, f"Expected 0 violations, got: {violations}")

if __name__ == "__main__":
    unittest.main()