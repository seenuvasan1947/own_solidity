// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract BadVisibility {
    function helper() public {
        // This function is never called externally
    }
    
    function doSomething() public {
        // Calls helper internally
        helper();
    }
} 