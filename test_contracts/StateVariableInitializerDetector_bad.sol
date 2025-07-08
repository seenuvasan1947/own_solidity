pragma solidity ^0.8.0;

contract BadContract {
    uint256 uninitializedVar;
    
    function doSomething() public {
        // some logic
    }
}