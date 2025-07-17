// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract BadInputs {
    uint public maxValue = 100;

    function setValue(uint value) public {
        // No validation for input "value"
        // simply assign it
        maxValue = value;
    }
    
    function deposit(uint amount) public {
        // No validation on input 'amount'
        // just accepting
    }
}
