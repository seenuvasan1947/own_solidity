// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract BadAccessControl {
    uint public counter = 0;
    function increment() public {
        counter += 1; // No access control
    }
    function setValue(uint v) public {
        counter = v; // No access control
    }
}
