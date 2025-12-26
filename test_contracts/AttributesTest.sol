// SPDX-License-Identifier: MIT
pragma solidity ^0.7.0;  // S-ATR-004: Old version

// Test contract for attribute detectors

// S-ATR-005: Locked Ether
contract LockedEtherContract {
    function deposit() public payable {
        // Can receive ether but no way to withdraw
    }
}

// S-ATR-001 & S-ATR-002: View function with assembly and state modification
contract ViewFunctionIssues {
    uint public counter;
    
    // S-ATR-001: View function with assembly
    function getWithAssembly() public view returns (uint) {
        assembly {
            let x := 1
        }
        return counter;
    }
    
    // S-ATR-002: View function modifying state
    function badView() public view returns (uint) {
        counter = counter + 1;  // BAD: Modifies state
        return counter;
    }
}

// S-ATR-006: Missing inheritance
interface IToken {
    function transfer(address to, uint amount) external returns (bool);
    function balanceOf(address account) external view returns (uint);
}

contract Token {  // Should inherit from IToken
    mapping(address => uint) balances;
    
    function transfer(address to, uint amount) external returns (bool) {
        balances[msg.sender] -= amount;
        balances[to] += amount;
        return true;
    }
    
    function balanceOf(address account) external view returns (uint) {
        return balances[account];
    }
}

// GOOD: Contract with withdrawal mechanism
contract GoodContract {
    address owner;
    
    constructor() {
        owner = msg.sender;
    }
    
    function deposit() public payable {}
    
    function withdraw() public {
        require(msg.sender == owner);
        payable(owner).transfer(address(this).balance);
    }
}
