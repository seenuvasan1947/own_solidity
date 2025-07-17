 // SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract GoodComments {
    uint public value;
    address public owner;
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }
    
    constructor() {
        owner = msg.sender;
    }
    
    // Function that modifies state
    function setValue(uint newValue) public onlyOwner {
        // Validates input before setting
        require(newValue > 0, "Value must be positive");
        value = newValue;
    }
    
    // View function that only reads data
    function getValue() public view returns (uint) {
        return value;
    }
}