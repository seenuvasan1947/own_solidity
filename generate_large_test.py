"""
Script to generate a large Solidity file for testing the bug detector
with 70k+ lines to ensure no content is skipped.
"""

def generate_large_solidity_file(output_path, target_lines=70000):
    """
    Generate a large Solidity file with various patterns to test.
    
    Args:
        output_path: Path where to save the generated file
        target_lines: Target number of lines (default: 70000)
    """
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # Write header
        f.write("// SPDX-License-Identifier: MIT\n")
        f.write("pragma solidity ^0.8.0;\n\n")
        
        # Calculate how many contracts we need
        lines_per_contract = 150  # Increased from 100 to generate more lines
        num_contracts = (target_lines - 10) // lines_per_contract
        
        print(f"Generating {num_contracts} contracts to reach ~{target_lines} lines...")
        
        for i in range(num_contracts):
            contract_num = i + 1
            
            # Every 100th contract has vulnerabilities
            has_vuln = (i % 100 == 0)
            
            f.write(f"// Contract {contract_num}\n")
            f.write(f"contract TestContract{contract_num} {{\n")
            f.write(f"    address public owner;\n")
            f.write(f"    uint256 public value{contract_num};\n")
            f.write(f"    mapping(address => uint256) public balances{contract_num};\n\n")
            
            # Constructor
            f.write(f"    constructor() {{\n")
            f.write(f"        owner = msg.sender;\n")
            f.write(f"        value{contract_num} = 0;\n")
            f.write(f"    }}\n\n")
            
            # Safe function with access control
            f.write(f"    modifier onlyOwner() {{\n")
            f.write(f"        require(msg.sender == owner, \"Not owner\");\n")
            f.write(f"        _;\n")
            f.write(f"    }}\n\n")
            
            f.write(f"    function safeFunction{contract_num}() public onlyOwner {{\n")
            f.write(f"        value{contract_num} += 1;\n")
            f.write(f"    }}\n\n")
            
            # Add vulnerable function every 100 contracts
            if has_vuln:
                f.write(f"    // VULNERABLE: No access control\n")
                f.write(f"    function dangerousFunction{contract_num}() public {{\n")
                f.write(f"        address(this).call{{value: 1 ether}}(\"\");\n")
                f.write(f"        value{contract_num} = 999;\n")
                f.write(f"    }}\n\n")
                
                f.write(f"    // VULNERABLE: selfdestruct without protection\n")
                f.write(f"    function destroyContract{contract_num}() external {{\n")
                f.write(f"        selfdestruct(payable(tx.origin));\n")
                f.write(f"    }}\n\n")
            
            # Regular functions
            f.write(f"    function getValue{contract_num}() public view returns (uint256) {{\n")
            f.write(f"        return value{contract_num};\n")
            f.write(f"    }}\n\n")
            
            f.write(f"    function setValue{contract_num}(uint256 newValue) public onlyOwner {{\n")
            f.write(f"        value{contract_num} = newValue;\n")
            f.write(f"    }}\n\n")
            
            f.write(f"    function deposit{contract_num}() public payable {{\n")
            f.write(f"        balances{contract_num}[msg.sender] += msg.value;\n")
            f.write(f"    }}\n\n")
            
            f.write(f"    function withdraw{contract_num}(uint256 amount) public {{\n")
            f.write(f"        require(balances{contract_num}[msg.sender] >= amount, \"Insufficient balance\");\n")
            f.write(f"        balances{contract_num}[msg.sender] -= amount;\n")
            f.write(f"        payable(msg.sender).transfer(amount);\n")
            f.write(f"    }}\n\n")
            
            # Internal helper function
            f.write(f"    function _internalHelper{contract_num}() internal pure returns (uint256) {{\n")
            f.write(f"        return {contract_num};\n")
            f.write(f"    }}\n\n")
            
            # Private helper function
            f.write(f"    function _privateHelper{contract_num}() private pure returns (uint256) {{\n")
            f.write(f"        return {contract_num} * 2;\n")
            f.write(f"    }}\n\n")
            
            # Event
            f.write(f"    event ValueChanged{contract_num}(uint256 oldValue, uint256 newValue);\n\n")
            
            # Struct
            f.write(f"    struct Data{contract_num} {{\n")
            f.write(f"        uint256 id;\n")
            f.write(f"        address user;\n")
            f.write(f"        uint256 timestamp;\n")
            f.write(f"    }}\n\n")
            
            # Mapping with struct
            f.write(f"    mapping(uint256 => Data{contract_num}) public dataStore{contract_num};\n\n")
            
            f.write(f"}}\n\n")
            
            # Progress indicator
            if (i + 1) % 100 == 0:
                print(f"  Generated {i + 1} contracts...")
        
        # Get final line count
        f.seek(0)
        
    # Count actual lines
    with open(output_path, 'r', encoding='utf-8') as f:
        actual_lines = sum(1 for _ in f)
    
    print(f"\n✓ Generated file: {output_path}")
    print(f"✓ Total lines: {actual_lines:,}")
    print(f"✓ Total contracts: {num_contracts}")
    print(f"✓ Contracts with vulnerabilities: {num_contracts // 100}")
    
    return actual_lines

if __name__ == "__main__":
    import os
    
    # Generate test file
    output_file = "test_contracts/large_test_70k.sol"
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Generate the file
    lines = generate_large_solidity_file(output_file, target_lines=70000)
    
    print(f"\nYou can now test with:")
    print(f"  python bug_detection_solidity.py {output_file}")
