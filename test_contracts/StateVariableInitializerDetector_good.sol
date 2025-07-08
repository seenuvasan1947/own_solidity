pragma solidity ^0.8.0;

contract GoodContract {
    uint256 initializedVar;

    constructor() {
        initializedVar = 1; // Properly initialized
    }
    
    function doSomething() public {
        // some logic
    }
}