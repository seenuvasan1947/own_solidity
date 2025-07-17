// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract BadAccess {
    uint public data;
    function changeData(uint _val) public {
        data = _val; // No check on msg.sender - any actor can call
    }
}
