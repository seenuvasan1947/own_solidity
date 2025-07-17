// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract GoodAccess {
    address public owner;
    uint public data;

    constructor() {
        owner = msg.sender;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    function changeData(uint _val) public onlyOwner {
        data = _val;
    }
}
