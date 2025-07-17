import unittest
from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from rules.AcesscontrolDetector import AccessControlDetector

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

class TestAccessControlDetector(unittest.TestCase):
    def test_detects_missing_access_control(self):
        violations = run_rule_on_file("test_contracts/AccessControlDetector_bad.sol", AccessControlDetector)
        self.assertGreater(len(violations), 0, "Expected violations for unprotected public/external functions")

    def test_ignores_protected_functions(self):
        violations = run_rule_on_file("test_contracts/AccessControlDetector_good.sol", AccessControlDetector)
        self.assertEqual(len(violations), 0, f"Expected no violations, got: {violations}")

if __name__ == "__main__":
    unittest.main()
