import unittest
import os
from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
from rules.UninitializedStateVariableDetector import UninitializedStateVariableDetector

def run_rule_on_file(filepath: str, rule_class: type[SolidityParserListener]):
    """
    Helper function to run an ANTLR listener-based rule on a Solidity file.
    """
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
    """
    Unit tests for the UninitializedStateVariableDetector rule.
    """
    # Define paths for test contracts
    TEST_CONTRACTS_DIR = "test_contracts"
    BAD_CONTRACT_PATH = os.path.join(TEST_CONTRACTS_DIR, "UninitializedStateVariableDetector_bad.sol")
    GOOD_CONTRACT_PATH = os.path.join(TEST_CONTRACTS_DIR, "UninitializedStateVariableDetector_good.sol")

    @classmethod
    def setUpClass(cls):
        """Create test_contracts directory and files before running tests."""
        os.makedirs(cls.TEST_CONTRACTS_DIR, exist_ok=True)

        bad_contract_content = """
pragma solidity ^0.8.0;

contract UninitializedBad {
    uint public uninitializedUint;
    address private uninitializedAddress;
    bool public uninitializedBool;
    string internal uninitializedString;
    bytes uninitializedBytes;
    int256 uninitializedInt;

    uint public valueSetInConstructor;
    address public owner;

    constructor() {
        valueSetInConstructor = 123;
        owner = msg.sender;
    }

    function getUninitializedUint() public view returns (uint) {
        return uninitializedUint;
    }

    function getUninitializedAddress() public view returns (address) {
        return uninitializedAddress;
    }
}
        """
        with open(cls.BAD_CONTRACT_PATH, "w") as f:
            f.write(bad_contract_content.strip())

        good_contract_content = """
pragma solidity ^0.8.0;

contract InitializedGood {
    uint public initializedUint = 1;
    address private initializedAddress = address(0x123);
    bool public initializedBool = true;
    string internal initializedString = "Hello, world!";
    bytes initializedBytes = hex"deadbeef";
    int256 initializedInt = -100;

    uint public valueSetInConstructor = 0;
    address public owner = address(0);

    constructor() {
        valueSetInConstructor = 456;
        owner = msg.sender;
    }

    function getInitializedUint() public view returns (uint) {
        return initializedUint;
    }

    function getOwner() public view returns (address) {
        return owner;
    }
}
        """
        with open(cls.GOOD_CONTRACT_PATH, "w") as f:
            f.write(good_contract_content.strip())

    @classmethod
    def tearDownClass(cls):
        """Clean up test files and directory after all tests are done."""
        os.remove(cls.BAD_CONTRACT_PATH)
        os.remove(cls.GOOD_CONTRACT_PATH)
        os.rmdir(cls.TEST_CONTRACTS_DIR)


    def test_detects_uninitialized_variables(self):
        """
        Tests if the detector correctly identifies all uninitialized state variables
        in the bad contract.
        """
        violations = run_rule_on_file(self.BAD_CONTRACT_PATH, UninitializedStateVariableDetector)

        # Expected variables to be flagged:
        # uninitializedUint, uninitializedAddress, uninitializedBool, uninitializedString,
        # uninitializedBytes, uninitializedInt, valueSetInConstructor, owner
        expected_uninitialized_vars = [
            "uninitializedUint", "uninitializedAddress", "uninitializedBool",
            "uninitializedString", "uninitializedBytes", "uninitializedInt",
            "valueSetInConstructor", "owner"
        ]

        self.assertEqual(len(violations), len(expected_uninitialized_vars),
                         f"Expected {len(expected_uninitialized_vars)} violations, got {len(violations)}: {violations}")

        for var_name in expected_uninitialized_vars:
            self.assertTrue(any(var_name in v for v in violations),
                            f"Violation for '{var_name}' not found in {violations}")

    def test_ignores_safe_contract(self):
        """
        Tests if the detector correctly ignores contracts where all state variables
        are explicitly initialized at declaration.
        """
        violations = run_rule_on_file(self.GOOD_CONTRACT_PATH, UninitializedStateVariableDetector)
        self.assertEqual(len(violations), 0, f"Expected no violations, but found: {violations}")

if __name__ == "__main__":
    unittest.main()