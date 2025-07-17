// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract BadOutputs {
    function getValue(uint x) public pure returns (uint result) {
        result = x * 2; // No validation of result
        return result;
    }
} 