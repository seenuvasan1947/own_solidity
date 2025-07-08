import unittest
import os
from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from rules.UninitializedStateVariableDetector import UninitializedStateVariableDetector

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

    @classmethod
    def setUpClass(cls):
        # Create a directory for test contracts if it doesn't exist
        os.makedirs("test_contracts", exist_ok=True)

        # Write the bad contract to a file
        cls.bad_contract_path = "test_contracts/UninitializedStateVariableDetector_bad.sol"
        with open(cls.bad_contract_path, "w") as f:
            f.write("""
pragma solidity ^0.8.0;

contract UninitializedContract {
    uint public myValue;
    address owner;
    string public contractName;
    uint256[] public dataArray;

    constructor() {
    }

    function doSomething() public {
    }
}
""")

        # Write the good contract to a file
        cls.good_contract_path = "test_contracts/UninitializedStateVariableDetector_good.sol"
        with open(cls.good_contract_path, "w") as f:
            f.write("""
pragma solidity ^0.8.0;

contract InitializedContract {
    uint public myValue = 100;
    address public owner;
    string public contractName = "MySafeContract";
    uint256[] public dataArray = new uint256[](0);

    constructor() {
        owner = msg.sender;
    }

    function doSomething() public view returns (uint) {
        return myValue;
    }
}
""")

    @classmethod
    def tearDownClass(cls):
        # Clean up the created files and directory
        os.remove(cls.bad_contract_path)
        os.remove(cls.good_contract_path)
        os.rmdir("test_contracts")


    def test_detects_uninitialized_variables(self):
        violations = run_rule_on_file(self.bad_contract_path, UninitializedStateVariableDetector)
        self.assertGreater(len(violations), 0, "Should detect uninitialized state variables")
        self.assertTrue(any("myValue" in v for v in violations))
        self.assertTrue(any("owner" in v for v in violations))
        self.assertTrue(any("contractName" in v for v in violations))
        self.assertTrue(any("dataArray" in v for v in violations))
        
        # Check specific line numbers for the bad contract
        # uint public myValue; // line 5
        # address owner; // line 7
        # string public contractName; // line 9
        # uint256[] public dataArray; // line 11
        violation_lines = {v.split('line ')[1].split(':')[0] for v in violations}
        self.assertIn('5', violation_lines)
        self.assertIn('7', violation_lines)
        self.assertIn('9', violation_lines)
        self.assertIn('11', violation_lines)


    def test_ignores_initialized_variables(self):
        violations = run_rule_on_file(self.good_contract_path, UninitializedStateVariableDetector)
        self.assertEqual(len(violations), 0, f"Should not detect violations in a properly initialized contract, but got: {violations}")

if __name__ == "__main__":
    unittest.main()