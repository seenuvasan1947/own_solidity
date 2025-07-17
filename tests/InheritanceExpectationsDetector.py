import unittest
from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from rules.InheritanceExpectationsDetector import InheritanceExpectationsDetector

def run_rule_on_file(filepath, rule_class):
    input_stream = FileStream(filepath)
    lexer = SolidityLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = SolidityParser(stream)
    tree = parser.sourceUnit()
    rule_instance = rule_class()
    
    # Pass the token stream to the detector if it has a set_token_stream method
    if hasattr(rule_instance, 'set_token_stream'):
        rule_instance.set_token_stream(stream)
    
    walker = ParseTreeWalker()
    walker.walk(rule_instance, tree)
    return rule_instance.get_violations()

class TestInheritanceExpectationsDetector(unittest.TestCase):
    def test_detects_missing_expected_functions(self):
        violations = run_rule_on_file("test_contracts/InheritanceExpectationsDetector_bad.sol", InheritanceExpectationsDetector)
        self.assertTrue(any("pause, unpause" in v for v in violations) or
                       any("extraFunc" in v for v in violations),
                        "Expected missing pause/unpause/extraFunc, got no violations")
    def test_passes_all_implemented(self):
        violations = run_rule_on_file("test_contracts/InheritanceExpectationsDetector_good.sol", InheritanceExpectationsDetector)
        self.assertEqual(len(violations), 0)
if __name__ == "__main__":
    unittest.main()
