import unittest
from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from rules.AccessControlFunctionDetector import AccessControlFunctionDetector

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

class TestAccessControlFunctionDetector(unittest.TestCase):
    def test_detects_missing_access_control(self):
        violations = run_rule_on_file("test_contracts/AccessControlFunctionDetector_bad.sol", AccessControlFunctionDetector)
        self.assertTrue(any("modifies state with no access control" in v for v in violations))
    def test_ignores_proper_access_control(self):
        violations = run_rule_on_file("test_contracts/AccessControlFunctionDetector_good.sol", AccessControlFunctionDetector)
        self.assertEqual(len(violations), 0)
if __name__ == "__main__":
    unittest.main()
