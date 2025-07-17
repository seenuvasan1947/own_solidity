// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract GoodVisibility {
    function doSomething() public {
        // This function is intended to be called externally
    }
    
    function callDoSomething() public {
        doSomething();
    }
} 