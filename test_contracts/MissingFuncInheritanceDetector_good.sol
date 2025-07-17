// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Pausable {
    bool public paused;
    // Intended for children to implement pause/unpause!
}
contract GoodInherited is Pausable {
    function pause() public { paused = true; }
    function unpause() public { paused = false; }
}
