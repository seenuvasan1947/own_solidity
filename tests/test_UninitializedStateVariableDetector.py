import unittest
import os
from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from rules.UninitializedStateVariableDetector import UninitializedStateVariableDetector  # import your rule

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
    # Class-level setup to create test contract files
    @classmethod
    def setUpClass(cls):
        # Create a directory for test contracts if it doesn't exist
        os.makedirs("test_contracts", exist_ok=True)

        cls.bad_contract_path = "test_contracts/UninitializedStateVariableDetector_bad.sol"
        cls.good_contract_path = "test_contracts/UninitializedStateVariableDetector_good.sol"

        # Write the content of the vulnerable contract to a file
        with open(cls.bad_contract_path, "w") as f:
            f.write("""
pragma solidity ^0.8.0;

contract VulnerableContract {
    // These state variables are declared but not explicitly initialized.
    // They will default to their zero-equivalent values (0, address(0), false).
    // This can be an oversight if a specific non-zero initial state is expected.
    uint public counter; 
    address public ownerAddress;
    bool public isActive;

    // An immutable variable. These can be initialized in the constructor,
    // so our refined rule should NOT flag this if it's not initialized at declaration.
    address immutable deployer;

    constructor() {
        // deployer = msg.sender; 
    }

    function increment() public {
        counter++;
    }

    function setOwner(address _newOwner) public {
        ownerAddress = _newOwner;
    }

    function getStatus() public view returns (uint, address, bool) {
        return (counter, ownerAddress, isActive);
    }
}
""")
        # Write the content of the safe contract to a file
        with open(cls.good_contract_path, "w") as f:
            f.write("""
pragma solidity ^0.8.0;

contract SafeContract {
    // All state variables are explicitly initialized at their declaration.
    // This ensures their initial values are clear and intended.
    uint public counter = 0; 
    address public ownerAddress = address(0);
    bool public isActive = false;

    // An immutable variable is declared without initialization at declaration,
    // but it is properly initialized in the constructor. This is a common and safe pattern.
    address immutable deployer; 

    constructor() {
        deployer = msg.sender; // Immutable variable initialized in the constructor.
    }

    function increment() public {
        counter++;
    }

    function setOwner(address _newOwner) public {
        ownerAddress = _newOwner;
    }

    function getStatus() public view returns (uint, address, bool) {
        return (counter, ownerAddress, isActive);
    }
}
""")
    
    # Class-level teardown to clean up test contract files
    @classmethod
    def tearDownClass(cls):
        os.remove(cls.bad_contract_path)
        os.remove(cls.good_contract_path)
        os.rmdir("test_contracts")


    def test_detects_uninitialized_state_variables(self):
        # Run the detector on the vulnerable contract
        violations = run_rule_on_file(self.bad_contract_path, UninitializedStateVariableDetector)
        
        # We expect 3 violations for 'counter', 'ownerAddress', and 'isActive'.
        # The 'deployer' (immutable) should NOT be flagged by the refined rule.
        self.assertEqual(len(violations), 3, f"Expected 3 violations, but got {len(violations)}: {violations}")
        
        # Verify that specific variable names are present in the violation messages
        violation_messages = [v.split("' at line")[0].split("variable '")[1] for v in violations]
        self.assertIn("counter", violation_messages)
        self.assertIn("ownerAddress", violation_messages)
        self.assertIn("isActive", violation_messages)
        self.assertNotIn("deployer", violation_messages) # Ensure immutable is not flagged

    def test_ignores_safe_contract(self):
        # Run the detector on the safe contract
        violations = run_rule_on_file(self.good_contract_path, UninitializedStateVariableDetector)
        
        # We expect 0 violations because all relevant state variables are initialized
        # and the immutable variable is handled correctly by the rule logic.
        self.assertEqual(len(violations), 0, f"Expected 0 violations, but got {len(violations)}: {violations}")

if __name__ == "__main__":
    unittest.main()