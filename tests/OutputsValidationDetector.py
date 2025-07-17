import unittest
from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from rules.OutputsValidationDetector import OutputsValidationDetector

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

class TestOutputsValidationDetector(unittest.TestCase):
    def test_detects_missing_output_validation(self):
        violations = run_rule_on_file("test_contracts/OutputsValidationDetector_bad.sol", OutputsValidationDetector)
        self.assertTrue(any("Missing output validation" in v for v in violations))

    def test_passes_validated(self):
        violations = run_rule_on_file("test_contracts/OutputsValidationDetector_good.sol", OutputsValidationDetector)
        self.assertEqual(len(violations), 0, f"Expected 0 violations, got: {violations}")

if __name__ == "__main__":
    unittest.main() 