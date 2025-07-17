import unittest
from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from rules.InheritanceVisibilityDetector import InheritanceVisibilityDetector

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

class TestInheritanceVisibilityDetector(unittest.TestCase):
    def test_detects_unrestricted_parent_funcs(self):
        violations = run_rule_on_file("test_contracts/InheritanceVisibilityDetector_bad.sol", InheritanceVisibilityDetector)
        print("Violations:", violations)
        self.assertTrue(any("not overridden/limited" in v for v in violations))
    def test_ignores_limited_inherited(self):
        violations = run_rule_on_file("test_contracts/InheritanceVisibilityDetector_good.sol", InheritanceVisibilityDetector)
        self.assertEqual(len(violations), 0)
if __name__ == "__main__":
    unittest.main()
