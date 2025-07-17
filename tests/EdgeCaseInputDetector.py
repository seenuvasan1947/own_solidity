import unittest
from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from rules.EdgeCaseInputDetector import EdgeCaseInputDetector

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

class TestEdgeCaseInputDetector(unittest.TestCase):
    def test_detects_missing_edge_case_validation(self):
        violations = run_rule_on_file("test_contracts/EdgeCaseInputDetector_bad.sol", EdgeCaseInputDetector)
        self.assertTrue(any("Missing edge case validation" in v for v in violations))

    def test_passes_edge_case_validation(self):
        violations = run_rule_on_file("test_contracts/EdgeCaseInputDetector_good.sol", EdgeCaseInputDetector)
        self.assertEqual(len(violations), 0, f"Expected 0 violations, got: {violations}")

if __name__ == "__main__":
    unittest.main() 