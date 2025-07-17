// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Pausable {
    function _requirePauseFuncs() internal virtual;
    bool public paused;
    // Intended for children to implement pause/unpause!
}
contract BadInherited is Pausable {
    // No implementation of pause/unpause!
}
