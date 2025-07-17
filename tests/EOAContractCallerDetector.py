import unittest
from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from rules.EOAContractCallerDetector import EOAContractCallerDetector

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

class TestEOAContractCallerDetector(unittest.TestCase):
    def test_detects_eoa_restriction(self):
        violations = run_rule_on_file("test_contracts/EOAContractCallerDetector_bad.sol", EOAContractCallerDetector)
        self.assertTrue(any("EOA" in v for v in violations))

    def test_detects_contract_check(self):
        violations = run_rule_on_file("test_contracts/EOAContractCallerDetector_iscontract.sol", EOAContractCallerDetector)
        self.assertTrue(any("contract detection" in v for v in violations))

    def test_ignores_safe(self):
        violations = run_rule_on_file("test_contracts/EOAContractCallerDetector_good.sol", EOAContractCallerDetector)
        self.assertEqual(len(violations), 0, f"Expected 0 violations, got: {violations}")

if __name__ == "__main__":
    unittest.main()
