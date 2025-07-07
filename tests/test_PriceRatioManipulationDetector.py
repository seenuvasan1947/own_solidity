import unittest
from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from rules.PriceRatioManipulationDetector import PriceRatioManipulationDetector  # import your rule
import os

def run_rule_on_file(filepath, rule_class):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    input_stream = FileStream(filepath)
    lexer = SolidityLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = SolidityParser(stream)
    tree = parser.sourceUnit()

    rule_instance = rule_class()
    walker = ParseTreeWalker()
    walker.walk(rule_instance, tree)

    return rule_instance.get_violations()

class TestPriceRatioManipulationDetector(unittest.TestCase):

    def setUp(self):
        # Create test_contracts directory if it doesn't exist
        if not os.path.exists("test_contracts"):
            os.makedirs("test_contracts")

        # Write bad contract to file
        with open("test_contracts/PriceRatioManipulationDetector_bad.sol", "w") as f:
            f.write("""
pragma solidity ^0.8.0;

interface IDEX {
    function getReserves() external view returns (uint112 reserve0, uint112 reserve1, uint32 blockTimestampLast);
}

contract PriceManipulation {
    IDEX public dex;

    constructor(address _dex) {
        dex = IDEX(_dex);
    }

    function calculatePrice() public view returns (uint) {
        (uint112 reserve0, uint112 reserve1, ) = dex.getReserves();
        require(reserve1 > 0, "Reserve1 cannot be zero");
        return reserve0 / reserve1;
    }
}
""")
        # Write good contract to file
        with open("test_contracts/PriceRatioManipulationDetector_good.sol", "w") as f:
            f.write("""
pragma solidity ^0.8.0;

contract SafePriceCalculation {
    uint public lastPrice;

    function updatePrice(uint newPrice) public {
        lastPrice = newPrice;
    }

    function calculatePrice() public view returns (uint) {
        //Returning a stored price that is ideally sourced from a TWAP oracle
        return lastPrice;
    }
}
""")

    def test_detects_price_manipulation(self):
        violations = run_rule_on_file("test_contracts/PriceRatioManipulationDetector_bad.sol", PriceRatioManipulationDetector)
        self.assertTrue(any("getReserves" in v for v in violations))

    def test_ignores_safe_contract(self):
        violations = run_rule_on_file("test_contracts/PriceRatioManipulationDetector_good.sol", PriceRatioManipulationDetector)
        self.assertEqual(len(violations), 0, f"Expected 0 violations, got: {violations}")

    def tearDown(self):
        # Remove test files and directory
        if os.path.exists("test_contracts/PriceRatioManipulationDetector_bad.sol"):
            os.remove("test_contracts/PriceRatioManipulationDetector_bad.sol")
        if os.path.exists("test_contracts/PriceRatioManipulationDetector_good.sol"):
            os.remove("test_contracts/PriceRatioManipulationDetector_good.sol")
        if os.path.exists("test_contracts"):
            os.rmdir("test_contracts")



if __name__ == "__main__":
    unittest.main()