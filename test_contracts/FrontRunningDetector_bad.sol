// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract BadFrontRunning {
    uint public value;
    
    function setValue(uint newValue) public {
        // Vulnerable to front-running: no protection mechanisms
        value = newValue;
    }
    
    function incrementValue() public {
        // Also vulnerable: modifies state without protection
        value++;
    }
} 