// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract GoodArbitraryInput {
    address public owner;
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }
    
    constructor() {
        owner = msg.sender;
    }
    
    function safeCall(address target, bytes4 selector) public onlyOwner {
        // Safe: restricted to specific function selector, not arbitrary data
        (bool success, ) = target.call(abi.encodeWithSelector(selector));
        require(success, "Call failed");
    }
    
    function getValue() public view returns (uint) {
        // Safe: no low-level calls
        return 42;
    }
} 