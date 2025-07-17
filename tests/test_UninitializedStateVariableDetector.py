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
    # Ensure test_contracts directory exists
    @classmethod
    def setUpClass(cls):
        os.makedirs("test_contracts", exist_ok=True)
        
        # Create bad contract file
        bad_contract_code = """
pragma solidity ^0.8.0;

contract UninitializedStateVariableBad {
    uint public myUint;
    address owner;
    bool public isActive;
    string public contractName;
    bytes memory someBytes; 

    uint public count; 

    constructor() {
        count = 0;
    }

    function doSomething() public {
    }
}
"""
        with open("test_contracts/UninitializedStateVariableDetector_bad.sol", "w") as f:
            f.write(bad_contract_code)

        # Create good contract file
        good_contract_code = """
pragma solidity ^0.8.0;

contract UninitializedStateVariableGood {
    uint public myUint = 0;
    address public owner = address(0);
    bool public isActive = false;
    string public contractName = "GoodContract";
    bytes public someBytes = hex"";
    uint public count = 1; 

    constructor() {
    }

    function doSomething() public view returns (uint) {
        return myUint + count;
    }
}
"""
        with open("test_contracts/UninitializedStateVariableDetector_good.sol", "w") as f:
            f.write(good_contract_code)

    # @classmethod
    # def tearDownClass(cls):
        # Clean up created files and directory
        # os.remove("test_contracts/UninitializedStateVariableDetector_bad.sol")
        # os.remove("test_contracts/UninitializedStateVariableDetector_good.sol")
        # os.rmdir("test_contracts")


    def test_detects_uninitialized_variables(self):
        violations = run_rule_on_file("test_contracts/UninitializedStateVariableDetector_bad.sol", UninitializedStateVariableDetector)
        self.assertGreater(len(violations), 0, "Expected violations in vulnerable contract")
        
        # Check for specific uninitialized variables
        expected_variables = ["owner", "balance", "isActive"]
        found_variables = []
        
        for violation in violations:
            for var in expected_variables:
                if var in violation:
                    found_variables.append(var)
        
        # Verify all expected variables were found
        for var in expected_variables:
            self.assertIn(var, found_variables, f"Expected uninitialized variable '{var}' not detected")

    def test_ignores_safe_contract(self):
        violations = run_rule_on_file("test_contracts/UninitializedStateVariableDetector_good.sol", UninitializedStateVariableDetector)
        self.assertEqual(len(violations), 0, f"Expected no violations in safe contract, but got: {violations}")

if __name__ == '__main__':
    unittest.main()