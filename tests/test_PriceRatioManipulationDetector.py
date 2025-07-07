import unittest
import os
from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from rules.PriceRatioManipulationDetector import PriceRatioManipulationDetector  # import your rule

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

class TestCommitRevealDetector(unittest.TestCase):
    CONTRACT_DIR = "test_contracts"

    @classmethod
    def setUpClass(cls):
        # Create the test_contracts directory if it doesn't exist
        if not os.path.exists(cls.CONTRACT_DIR):
            os.makedirs(cls.CONTRACT_DIR)

        # Create dummy lexer and parser in test_contracts directory
        # so that antlr can find and run it.
        with open(os.path.join(cls.CONTRACT_DIR, "SolidityLexer.py"), 'w') as f:
             f.write("class SolidityLexer: pass")
        with open(os.path.join(cls.CONTRACT_DIR, "SolidityParser.py"), 'w') as f:
             f.write("class SolidityParser: \n    def sourceUnit(self): return None")


        # Create the bad and good contracts within the test_contracts directory
        with open(os.path.join(cls.CONTRACT_DIR, "PriceRatioManipulationDetector_bad.sol"), "w") as f:
            f.write("""
pragma solidity ^0.8.0;

contract VulnerableContract {
    address token0;
    address token1;

    constructor(address _token0, address _token1) {
        token0 = _token0;
        token1 = _token1;
    }

    function getPrice() public view returns (uint256) {
        // Vulnerable: Price calculated directly from token balances.
        uint256 price = token0.balance(address(this)) / token1.balance(address(this));
        return price;
    }
}
            """)

        with open(os.path.join(cls.CONTRACT_DIR, "PriceRatioManipulationDetector_good.sol"), "w") as f:
            f.write("""
pragma solidity ^0.8.0;

contract SafeContract {
    uint256 public price;

    function setPrice(uint256 _price) public {
        price = _price;
    }

    function getPrice() public view returns (uint256) {
        // Safe: Price is not directly derived from token balances.
        return price;
    }
}
            """)

    @classmethod
    def tearDownClass(cls):
         # Clean up files first
        for filename in os.listdir(cls.CONTRACT_DIR):
            file_path = os.path.join(cls.CONTRACT_DIR, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))

        # Then remove the directory
        os.rmdir(cls.CONTRACT_DIR)

    def test_detects_vulnerability(self):
        violations = run_rule_on_file(os.path.join(self.CONTRACT_DIR, "PriceRatioManipulationDetector_bad.sol"), PriceRatioManipulationDetector)
        self.assertTrue(any("Price calculated by ratio of token balances" in v for v in violations))

    def test_ignores_safe_contract(self):
        violations = run_rule_on_file(os.path.join(self.CONTRACT_DIR, "PriceRatioManipulationDetector_good.sol"), PriceRatioManipulationDetector)
        self.assertEqual(len(violations), 0, f"Expected 0 violations, got: {violations}")

if __name__ == "__main__":
    import shutil
    unittest.main()