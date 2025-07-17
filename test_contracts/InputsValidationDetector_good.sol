// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract GoodInputs {
    uint public maxValue = 100;

    function setValue(uint value) public {
        require(value > 0 && value <= 1000, "value out of range");
        maxValue = value;
    }

    function deposit(uint amount) public {
        require(amount > 0, "amount must be positive");
        // proceed...
    }
}
