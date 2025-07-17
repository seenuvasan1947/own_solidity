// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract GoodFrontRunning {
    uint public value;
    address public owner;
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }
    
    constructor() {
        owner = msg.sender;
    }
    
    function setValue(uint newValue) public onlyOwner {
        // Protected by onlyOwner modifier
        value = newValue;
    }
    
    function incrementValue() public {
        require(msg.sender == owner, "Not authorized");
        value++;
    }
} 