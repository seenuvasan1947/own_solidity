import unittest
from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from rules.FrontRunningDetector import FrontRunningDetector

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

class TestFrontRunningDetector(unittest.TestCase):
    def test_detects_front_running_vulnerability(self):
        violations = run_rule_on_file("test_contracts/FrontRunningDetector_bad.sol", FrontRunningDetector)
        self.assertTrue(any("front-running vulnerability" in v for v in violations))

    def test_passes_safe_contract(self):
        violations = run_rule_on_file("test_contracts/FrontRunningDetector_good.sol", FrontRunningDetector)
        self.assertEqual(len(violations), 0, f"Expected 0 violations, got: {violations}")

if __name__ == "__main__":
    unittest.main() 