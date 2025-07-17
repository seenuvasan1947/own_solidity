import unittest
from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from rules.CommentsCoherenceDetector import CommentsCoherenceDetector

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

class TestCommentsCoherenceDetector(unittest.TestCase):
    def test_detects_incoherent_comments(self):
        violations = run_rule_on_file("test_contracts/CommentsCoherenceDetector_bad.sol", CommentsCoherenceDetector)
        self.assertTrue(any("Comment coherence issue" in v for v in violations))

    def test_passes_coherent_comments(self):
        violations = run_rule_on_file("test_contracts/CommentsCoherenceDetector_good.sol", CommentsCoherenceDetector)
        self.assertEqual(len(violations), 0, f"Expected 0 violations, got: {violations}")

if __name__ == "__main__":
    unittest.main()