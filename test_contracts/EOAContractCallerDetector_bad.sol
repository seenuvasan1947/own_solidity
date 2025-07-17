// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract OnlyEOA {
    uint public data;
    function setData(uint _val) public {
        require(msg.sender == tx.origin, "Only EOA allowed");
        data = _val;
    }
}

