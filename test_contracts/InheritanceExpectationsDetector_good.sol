// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/** expected_func: pause, unpause */
contract Pausable {
    function pause() external virtual {}
    function unpause() external virtual {}
}
/** expected_func: extraFunc */
contract MyContract is Pausable {
    function pause() external override {}
    function unpause() external override {}
    function extraFunc() external {}
}
