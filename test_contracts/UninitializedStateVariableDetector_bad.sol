
pragma solidity ^0.8.0;

contract UninitializedStateVariableBad {
    uint public myUint;
    address owner;
    bool public isActive;
    string public contractName;
    bytes memory someBytes; 

    uint public count; 

    constructor() {
        count = 0;
    }

    function doSomething() public {
    }
}
