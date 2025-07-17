// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract GoodEdgeCases {
    uint public value;
    
    function setValue(uint newValue) public {
        // Validates edge cases
        require(newValue > 0, "Value must be greater than 0");
        require(newValue <= type(uint256).max, "Value exceeds maximum");
        value = newValue;
    }
    
    function divide(uint numerator, uint denominator) public pure returns (uint) {
        // Validates division by zero
        require(denominator != 0, "Division by zero");
        return numerator / denominator;
    }
} 