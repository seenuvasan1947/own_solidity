
pragma solidity ^0.8.0;

contract UninitializedStateVariableGood {
    uint public myUint = 0;
    address public owner = address(0);
    bool public isActive = false;
    string public contractName = "GoodContract";
    bytes public someBytes = hex"";
    uint public count = 1; 

    constructor() {
    }

    function doSomething() public view returns (uint) {
        return myUint + count;
    }
}
