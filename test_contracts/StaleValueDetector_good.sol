pragma solidity ^0.8.0;

contract SafeContract {
    uint256 public value;
    bool public locked;

    constructor() {
        value = 100;
        locked = false;
    }

    function getValue() public view returns (uint256) {
        // No direct state variable access, or use a reentrancy guard
        uint256 tempValue = value; // Local variable, not a direct state access
        return tempValue;
    }

    function setValue(uint256 newValue) public {
        require(!locked, "Contract is locked");
        locked = true;
        value = newValue;
        locked = false;
    }
}