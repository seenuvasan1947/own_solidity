import unittest
from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from rules.InputsValidationDetector import InputsValidationDetector

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

class TestInputsValidationDetector(unittest.TestCase):
    def test_detects_missing_validation(self):
        violations = run_rule_on_file("test_contracts/InputsValidationDetector_bad.sol", InputsValidationDetector)
        self.assertTrue(any("Missing input validation" in v for v in violations))

    def test_passes_validated(self):
        violations = run_rule_on_file("test_contracts/InputsValidationDetector_good.sol", InputsValidationDetector)
        self.assertEqual(len(violations), 0, f"Expected 0 violations, got: {violations}")

if __name__ == "__main__":
    unittest.main()
