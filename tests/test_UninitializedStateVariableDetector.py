import unittest
import os
from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from rules.UninitializedStateVariableDetector import UninitializedStateVariableDetector  # import your rule

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
    # Create a temporary directory for test contracts
    @classmethod
    def setUpClass(cls):
        cls.test_contracts_dir = "test_contracts"
        os.makedirs(cls.test_contracts_dir, exist_ok=True)

        cls.bad_contract_path = os.path.join(cls.test_contracts_dir, "UninitializedStateVariableDetector_bad.sol")
        with open(cls.bad_contract_path, "w") as f:
            f.write("""
pragma solidity ^0.8.0;

contract VulnerableInitialization {
    uint public uninitializedUint;
    bool public uninitializedBool;
    address public uninitializedAddress;
    bytes public uninitializedBytes;

    struct MyStruct {
        uint value;
        bool status;
    }

    MyStruct public myStruct;

    function doSomething() public {
        // ...
    }
}
            """)

        cls.good_contract_path = os.path.join(cls.test_contracts_dir, "UninitializedStateVariableDetector_good.sol")
        with open(cls.good_contract_path, "w") as f:
            f.write("""
pragma solidity ^0.8.0;

contract SafeInitialization {
    uint public initializedUint = 100;
    bool public initializedBool = true;
    address public initializedAddress = msg.sender;
    bytes public initializedBytes = "Hello";

    uint public constant MY_CONSTANT = 123;
    uint public immutable MY_IMMUTABLE_AT_DECLARATION = 456;
    uint public immutable MY_IMMUTABLE_IN_CONSTRUCTOR;

    struct MyStruct {
        uint value;
        bool status;
    }

    MyStruct public myStruct = MyStruct({value: 789, status: true});

    constructor() {
        MY_IMMUTABLE_IN_CONSTRUCTOR = 999;
    }

    function doSomething() public {
        // ...
    }
}
            """)

    # Clean up the temporary directory
    @classmethod
    def tearDownClass(cls):
        os.remove(cls.bad_contract_path)
        os.remove(cls.good_contract_path)
        os.rmdir(cls.test_contracts_dir)

    def test_detects_uninitialized_state_variables(self):
        violations = run_rule_on_file(self.bad_contract_path, UninitializedStateVariableDetector)
        
        # Expected violations: uninitializedUint, uninitializedBool, uninitializedAddress, uninitializedBytes, myStruct
        expected_variable_names = ["uninitializedUint", "uninitializedBool", "uninitializedAddress", "uninitializedBytes", "myStruct"]
        
        self.assertEqual(len(violations), len(expected_variable_names), f"Expected {len(expected_variable_names)} violations, got {len(violations)}: {violations}")
        
        for name in expected_variable_names:
            self.assertTrue(any(name in v for v in violations), f"Violation for '{name}' not found in {violations}")

    def test_ignores_safe_contract(self):
        violations = run_rule_on_file(self.good_contract_path, UninitializedStateVariableDetector)
        self.assertEqual(len(violations), 0, f"Expected 0 violations, got: {violations}")

if __name__ == "__main__":
    unittest.main()