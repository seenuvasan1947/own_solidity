 // SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract BadArbitraryInput {
    function executeCall(address target, bytes calldata data) public {
        // Risky: accepts arbitrary data and makes low-level call
        (bool success, ) = target.call(data);
        require(success, "Call failed");
    }
    
    function delegateCall(address target, bytes calldata data) public {
        // Also risky: arbitrary data with delegatecall
        (bool success, ) = target.delegatecall(data);
        require(success, "Delegatecall failed");
    }
}