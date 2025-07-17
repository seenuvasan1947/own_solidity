// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract OpenAccess {
    uint public data;
    function setData(uint _val) public {
        data = _val;
    }
}
