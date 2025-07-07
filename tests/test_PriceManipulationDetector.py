import unittest
import os
from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from rules.PriceManipulationDetector import PriceManipulationDetector  # import your rule

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

class TestPriceManipulationDetector(unittest.TestCase):

    def setUp(self):
        # Create test_contracts directory if it doesn't exist
        if not os.path.exists("test_contracts"):
            os.makedirs("test_contracts")

        # Create dummy contract files
        with open("test_contracts/PriceManipulationDetector_bad.sol", "w") as f:
            f.write("""
pragma solidity ^0.8.0;

interface IDEX {
    function getPrice() external view returns (uint);
}

contract VulnerableContract {
    IDEX public dex;

    constructor(address _dex) {
        dex = IDEX(_dex);
    }

    function calculateValue() public view returns (uint) {
        // Directly using DEX spot price. Vulnerable to manipulation.
        uint price = dex.getPrice();
        return price * 100;
    }
}
""")

        with open("test_contracts/PriceManipulationDetector_good.sol", "w") as f:
            f.write("""
pragma solidity ^0.8.0;

interface IOracle {
    function getPrice() external view returns (uint);
}

contract SafeContract {
    IOracle public oracle;

    constructor(address _oracle) {
        oracle = IOracle(_oracle);
    }

    function calculateValue() public view returns (uint) {
        // Using an oracle for price feed.
        uint price = oracle.getPrice();
        return price * 100;
    }
}
""")


    def test_detects_price_manipulation(self):
        violations = run_rule_on_file("test_contracts/PriceManipulationDetector_bad.sol", PriceManipulationDetector)
        self.assertTrue(any("Possible price manipulation" in v for v in violations), f"Violations found: {violations}")

    def test_ignores_safe_contract(self):
        violations = run_rule_on_file("test_contracts/PriceManipulationDetector_good.sol", PriceManipulationDetector)
        self.assertEqual(len(violations), 0, f"Violations found: {violations}")

    def tearDown(self):
        # Clean up the dummy contract files and directory after the tests
        os.remove("test_contracts/PriceManipulationDetector_bad.sol")
        os.remove("test_contracts/PriceManipulationDetector_good.sol")
        os.rmdir("test_contracts")



if __name__ == "__main__":
    # Create 'rules' directory if it doesn't exist before running tests
    if not os.path.exists("rules"):
        os.makedirs("rules")

    # Save PriceManipulationDetector.py inside 'rules' directory
    with open("rules/PriceManipulationDetector.py", "w") as f:
        f.write("""
from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class PriceManipulationDetector(SolidityParserListener):
    def __init__(self):
        self.violations = []

    def enterFunctionCall(self, ctx):
        # Look for function calls that might be getting spot prices directly.
        # This is a simplified check and can be refined with more specific DEX function names.
        function_text = ctx.getText().lower()
        if ("getprice" in function_text or "currentprice" in function_text or "getPrice" in function_text or "get_price" in function_text) and "twap" not in function_text:  # Add check to exclude TWAP
            line = ctx.start.line
            self.violations.append(f"❌ Possible price manipulation vulnerability at line {line}: Direct DEX price usage detected. Consider using TWAP or oracles. Function Call: {function_text}")

    def get_violations(self):
        return self.violations
""")


    unittest.main()