import unittest
from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from rules.AccessControlActorsDetector import AccessControlActorsDetector

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

class TestAccessControlActorsDetector(unittest.TestCase):
    def test_detects_missing_access_control(self):
        violations = run_rule_on_file("test_contracts/AccessControlActorsDetector_bad.sol", AccessControlActorsDetector)
        self.assertTrue(any("Unclear actor" in v for v in violations))

    def test_ignores_safe_contract(self):
        violations = run_rule_on_file("test_contracts/AccessControlActorsDetector_good.sol", AccessControlActorsDetector)
        self.assertEqual(len(violations), 0, f"Expected 0 violations, got: {violations}")

if __name__ == "__main__":
    unittest.main()
