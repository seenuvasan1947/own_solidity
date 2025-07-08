import unittest
import os
from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from rules.UninitializedStateVariableDetector import UninitializedStateVariableDetector

# Helper function to run the rule on a file
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

    # Set up test contract file paths
    TEST_CONTRACTS_DIR = "test_contracts"
    BAD_CONTRACT_PATH = os.path.join(TEST_CONTRACTS_DIR, "UninitializedStateVariableDetector_bad.sol")
    GOOD_CONTRACT_PATH = os.path.join(TEST_CONTRACTS_DIR, "UninitializedStateVariableDetector_good.sol")

    @classmethod
    def setUpClass(cls):
        # Ensure the test_contracts directory exists
        os.makedirs(cls.TEST_CONTRACTS_DIR, exist_ok=True)

        # Content for the vulnerable contract
        bad_contract_content = """
pragma solidity ^0.8.0;

contract VulnerableContract {
    uint public uninitializedUint;
    address public owner;
    string public contractName;
    bool public isActive;

    struct MyConfig {
        uint value;
        bool enabled;
    }
    MyConfig public config;

    mapping(address => uint) public balances;

    uint public initializedUint = 10;
    address private _admin = msg.sender;

    constructor() {
        owner = msg.sender;
    }

    function doSomething() public {
        // Contract logic
    }
}
        """
        # Content for the safe contract
        good_contract_content = """
pragma solidity ^0.8.0;

contract SafeContract {
    uint public initializedUint = 0;
    address public owner = address(0);
    string public contractName = "MySafeContract";
    bool public isActive = false;

    struct MyConfig {
        uint value;
        bool enabled;
    }
    MyConfig public config = MyConfig({value: 0, enabled: false});

    mapping(address => uint) public balances; // Mappings are inherently not initialized at declaration via '='

    constructor() {
        // owner = msg.sender;
    }

    function doSomething() public pure returns (string memory) {
        return "Contract is safe.";
    }
}
        """
        # Write contracts to files
        with open(cls.BAD_CONTRACT_PATH, "w") as f:
            f.write(bad_contract_content.strip())
        with open(cls.GOOD_CONTRACT_PATH, "w") as f:
            f.write(good_contract_content.strip())

    @classmethod
    def tearDownClass(cls):
        # Clean up the created files and directory after all tests are done
        os.remove(cls.BAD_CONTRACT_PATH)
        os.remove(cls.GOOD_CONTRACT_PATH)
        os.rmdir(cls.TEST_CONTRACTS_DIR)

    def test_detects_uninitialized_variables(self):
        violations = run_rule_on_file(self.BAD_CONTRACT_PATH, UninitializedStateVariableDetector)

        # Expected uninitialized variables based on the rule's definition:
        # uninitializedUint, owner, contractName, isActive, config, balances (mappings are flagged too)
        expected_violations_count = 6
        self.assertEqual(len(violations), expected_violations_count, f"Expected {expected_violations_count} violations, got {len(violations)}: {violations}")

        self.assertTrue(any("'uninitializedUint'" in v for v in violations))
        self.assertTrue(any("'owner'" in v for v in violations))
        self.assertTrue(any("'contractName'" in v for v in violations))
        self.assertTrue(any("'isActive'" in v for v in violations))
        self.assertTrue(any("'config'" in v for v in violations))
        self.assertTrue(any("'balances'" in v for v in violations)) # Mappings are flagged by this rule

    def test_ignores_safe_contract(self):
        violations = run_rule_on_file(self.GOOD_CONTRACT_PATH, UninitializedStateVariableDetector)

        # In the good contract, all non-mapping variables are explicitly initialized.
        # However, the `balances` mapping will still be flagged as mappings cannot be
        # initialized with an `=` operator at declaration.
        # So, we expect exactly 1 violation for the mapping.
        expected_violations_count = 1
        self.assertEqual(len(violations), expected_violations_count, f"Expected {expected_violations_count} violation, got: {violations}")
        self.assertTrue(any("'balances'" in v for v in violations)) # The mapping is the only expected violation
        self.assertFalse(any("'initializedUint'" in v for v in violations))
        self.assertFalse(any("'owner'" in v for v in violations))
        self.assertFalse(any("'contractName'" in v for v in violations))
        self.assertFalse(any("'isActive'" in v for v in violations))
        self.assertFalse(any("'config'" in v for v in violations))

if __name__ == "__main__":
    unittest.main()