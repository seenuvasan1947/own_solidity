"""
Quick script to generate exactly 70k+ lines for testing
"""

def generate_exact_70k_file(output_path):
    """Generate a file with exactly 70,000+ lines"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # Write header
        f.write("// SPDX-License-Identifier: MIT\n")
        f.write("pragma solidity ^0.8.0;\n\n")
        
        # Generate contracts until we reach 70k lines
        contract_num = 0
        lines_written = 3
        
        while lines_written < 70000:
            contract_num += 1
            has_vuln = (contract_num % 50 == 0)
            
            f.write(f"contract C{contract_num} {{\n")
            f.write(f"    address owner;\n")
            f.write(f"    uint256 val;\n")
            f.write(f"    constructor() {{ owner = msg.sender; }}\n")
            f.write(f"    modifier onlyOwner() {{ require(msg.sender == owner); _; }}\n")
            lines_written += 5
            
            # Add 50 functions per contract
            for i in range(50):
                if has_vuln and i == 0:
                    f.write(f"    function dangerous{i}() public {{\n")
                    f.write(f"        address(this).call{{value: 1 ether}}(\"\");\n")
                    f.write(f"    }}\n")
                else:
                    f.write(f"    function func{i}() public onlyOwner {{\n")
                    f.write(f"        val = {i};\n")
                    f.write(f"    }}\n")
                lines_written += 3
            
            if has_vuln:
                f.write(f"    function destroy() external {{\n")
                f.write(f"        selfdestruct(payable(tx.origin));\n")
                f.write(f"    }}\n")
                lines_written += 3
            
            f.write(f"}}\n\n")
            lines_written += 2
            
            if contract_num % 100 == 0:
                print(f"  Lines: {lines_written:,} / 70,000")
    
    # Count actual lines
    with open(output_path, 'r', encoding='utf-8') as f:
        actual_lines = sum(1 for _ in f)
    
    print(f"\n✓ Generated: {output_path}")
    print(f"✓ Total lines: {actual_lines:,}")
    print(f"✓ Total contracts: {contract_num}")
    
    return actual_lines

if __name__ == "__main__":
    import os
    output_file = "test_contracts/exact_70k_test.sol"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    generate_exact_70k_file(output_file)
