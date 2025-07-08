import unittest
from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from rules.StateVariableInitializationDetector import StateVariableInitializationDetector  # import your rule

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

class TestStateVariableInitializationDetector(unittest.TestCase):
    def test_detects_uninitialized_variable(self):
        violations = run_rule_on_file("test_contracts/StateVariableInitializationDetector_bad.sol", StateVariableInitializationDetector)
        self.assertTrue(any("Uninitialized state variable" in v for v in violations))

    def test_ignores_initialized_variable(self):
        violations = run_rule_on_file("test_contracts/StateVariableInitializationDetector_good.sol", StateVariableInitializationDetector)
        self.assertEqual(len(violations), 0)

if __name__ == "__main__":
    unittest.main()