// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract GoodOutputs {
    function getValue(uint x) public pure returns (uint result) {
        result = x * 2;
        require(result > 0, "Output must be positive");
        return result;
    }
} 