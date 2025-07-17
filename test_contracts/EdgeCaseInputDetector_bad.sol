// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract BadEdgeCases {
    uint public value;
    
    function setValue(uint newValue) public {
        // No validation for edge cases (0, max values)
        value = newValue;
    }
    
    function divide(uint numerator, uint denominator) public pure returns (uint) {
        // No validation for division by zero
        return numerator / denominator;
    }
} 