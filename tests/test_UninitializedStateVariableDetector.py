import unittest
import os
from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from rules.UninitializedStateVariableDetector import UninitializedStateVariableDetector

# Helper function to run the rule on a Solidity file
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

class TestUninitializedStateVariableDetector(unittest.TestCase):
    # Define paths for test contracts
    TEST_CONTRACTS_DIR = "test_contracts"
    BAD_CONTRACT_PATH = os.path.join(TEST_CONTRACTS_DIR, "UninitializedStateVariableDetector_bad.sol")
    GOOD_CONTRACT_PATH = os.path.join(TEST_CONTRACTS_DIR, "UninitializedStateVariableDetector_good.sol")

    @classmethod
    def setUpClass(cls):
        # Create test_contracts directory if it doesn't exist
        os.makedirs(cls.TEST_CONTRACTS_DIR, exist_ok=True)

        # Write the bad contract content to a file
        with open(cls.BAD_CONTRACT_PATH, "w") as f:
            f.write("""pragma solidity ^0.8.0;

contract VulnerableContract {
    uint256 public myNumber; // Not explicitly initialized
    address public owner;    // Not explicitly initialized
    bool private _isActive;  // Not explicitly initialized
    string public userName;  // Not explicitly initialized
    bytes public data;       // Not explicitly initialized
    
    constructor() {}

    function getMyNumber() public view returns (uint256) {
        return myNumber;
    }

    function getOwner() public view returns (address) {
        return owner;
    }

    function getIsActive() public view returns (bool) {
        return _isActive;
    }
}""")

        # Write the good contract content to a file
        with open(cls.GOOD_CONTRACT_PATH, "w") as f:
            f.write("""pragma solidity ^0.8.0;

contract SafeContract {
    uint256 public myNumber = 0;       // Explicitly initialized
    address public owner = address(0); // Explicitly initialized
    bool private _isActive = false;    // Explicitly initialized
    string public userName = "";       // Explicitly initialized
    bytes public data = hex"";         // Explicitly initialized

    uint256 public constant MAX_VALUE = 100;

    constructor() {}

    function getMyNumber() public view returns (uint256) {
        return myNumber;
    }

    function getOwner() public view returns (address) {
        return owner;
    }

    function getIsActive() public view returns (bool) {
        return _isActive;
    }
}""")

    @classmethod
    def tearDownClass(cls):
        # Clean up test contract files and directory
        os.remove(cls.BAD_CONTRACT_PATH)
        os.remove(cls.GOOD_CONTRACT_PATH)
        os.rmdir(cls.TEST_CONTRACTS_DIR)

    def test_detects_uninitialized_variables(self):
        violations = run_rule_on_file(self.BAD_CONTRACT_PATH, UninitializedStateVariableDetector)
        # Expected 5 violations for myNumber, owner, _isActive, userName, data
        self.assertEqual(len(violations), 5, f"Expected 5 violations, got: {violations}")
        self.assertTrue(any("'myNumber'" in v for v in violations))
        self.assertTrue(any("'owner'" in v for v in violations))
        self.assertTrue(any("'_isActive'" in v for v in violations))
        self.assertTrue(any("'userName'" in v for v in violations))
        self.assertTrue(any("'data'" in v for v in violations))


    def test_ignores_safe_contract(self):
        violations = run_rule_on_file(self.GOOD_CONTRACT_PATH, UninitializedStateVariableDetector)
        self.assertEqual(len(violations), 0, f"Expected 0 violations, got: {violations}")

if __name__ == "__main__":
    unittest.main()