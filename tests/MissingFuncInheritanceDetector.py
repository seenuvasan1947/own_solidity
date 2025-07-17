import unittest
from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from rules.MissingFuncInheritanceDetector import MissingFuncInheritanceDetector

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

class TestMissingFuncInheritanceDetector(unittest.TestCase):
    def setUp(self):
        from rules.MissingFuncInheritanceDetector import MissingFuncInheritanceDetector
        self.rule = MissingFuncInheritanceDetector
        self.rule = MissingFuncInheritanceDetector

    def test_detects_not_implemented(self):
        violations = run_rule_on_file("test_contracts/MissingFuncInheritanceDetector_bad.sol", self.rule)
        self.assertTrue(any("does not implement required function" in v for v in violations))
    def test_approves_implemented(self):
        violations = run_rule_on_file("test_contracts/MissingFuncInheritanceDetector_good.sol", self.rule)
        self.assertEqual(len(violations), 0)
if __name__ == "__main__":
    unittest.main()
