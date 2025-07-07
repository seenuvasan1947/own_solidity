import unittest
from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from rules.StaleValueDetector import StaleValueDetector  # import your rule
import os


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

class TestStaleValueDetector(unittest.TestCase):
    def setUp(self):
        # Create test_contracts directory if it doesn't exist
        if not os.path.exists("test_contracts"):
            os.makedirs("test_contracts")

        # Write the vulnerable contract to a file
        with open("test_contracts/StaleValueDetector_bad.sol", "w") as f:
            f.write("""
pragma solidity ^0.8.0;

interface IExternal {
    function getValue() external view returns (uint256);
}

contract VulnerableContract {
    IExternal public externalContract;
    uint256 public internalValue;

    constructor(IExternal _externalContract) {
        externalContract = _externalContract;
        internalValue = 100;
    }

    function getCombinedValue() public view returns (uint256) {
        // External contract might change its state between calls
        uint256 externalValue = externalContract.getValue();
        uint256 result = internalValue + externalValue;
        return result; // Possible stale value if externalValue changes after being read.
    }

    function setInternalValue(uint256 _newValue) public {
        internalValue = _newValue;
    }
}
""")

        # Write the safe contract to a file
        with open("test_contracts/StaleValueDetector_good.sol", "w") as f:
            f.write("""
pragma solidity ^0.8.0;

interface IExternal {
    function getValue() external view returns (uint256);
}

contract SafeContract {
    IExternal public externalContract;
    uint256 public internalValue;

    constructor(IExternal _externalContract) {
        externalContract = _externalContract;
        internalValue = 100;
    }

    function getInternalValue() public view returns (uint256) {
        return internalValue;
    }

    function setInternalValue(uint256 _newValue) public {
        internalValue = _newValue;
    }
}
""")


    def test_detects_stale_value(self):
        violations = run_rule_on_file("test_contracts/StaleValueDetector_bad.sol", StaleValueDetector)
        self.assertTrue(any("SOL-AM-DA-1" in v for v in violations), f"Expected stale value detection, got: {violations}")

    def test_ignores_safe_contract(self):
        violations = run_rule_on_file("test_contracts/StaleValueDetector_good.sol", StaleValueDetector)
        self.assertEqual(len(violations), 0, f"Expected no violations, got: {violations}")

    def tearDown(self):
        # Remove the test files and directory
        if os.path.exists("test_contracts/StaleValueDetector_bad.sol"):
            os.remove("test_contracts/StaleValueDetector_bad.sol")
        if os.path.exists("test_contracts/StaleValueDetector_good.sol"):
            os.remove("test_contracts/StaleValueDetector_good.sol")
        if os.path.exists("test_contracts"):
            os.rmdir("test_contracts")


if __name__ == "__main__":
    unittest.main()