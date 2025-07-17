// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract BadComments {
    uint public value;
    
    // Safe function that only reads data
    function setValue(uint newValue) public {
        // This comment is misleading - function actually modifies state
        value = newValue;
    }
    
    // Owner-only function with validation
    function incrementValue() public {
        // Comment suggests owner-only but function is public
        value++;
    }
    
    // View function that doesn't modify state
    function getValue() public view returns (uint) {
        // This comment is correct
        return value;
    }
}