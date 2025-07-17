// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract GoodAccessControl {
    uint public counter = 0;
    address public owner;
    constructor() { owner = msg.sender; }
    modifier onlyOwner() { require(msg.sender == owner, "not the owner"); _; }
    function increment() public onlyOwner {
        counter += 1;
    }
    function setValue(uint v) public onlyOwner {
        counter = v;
    }
}
