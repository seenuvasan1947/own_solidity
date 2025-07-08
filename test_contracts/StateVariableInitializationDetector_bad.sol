pragma solidity ^0.8.0;

contract BadContract {
    uint256 uninitializedVariable;

    function doSomething() public {
        // No operation
    }
}