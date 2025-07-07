pragma solidity ^0.8.0;

contract SafeContract {
    uint256 public value;
    address public owner;
    bool private locked;

    constructor() {
        owner = msg.sender;
        value = 10;
        locked = false;
    }

    modifier noReentrancy() {
        require(!locked, "Reentrant call");
        locked = true;
        _;
        locked = false;
    }


    function getValue() public view noReentrancy returns (uint256) {
        return value;
    }

    function changeValue(uint256 newValue) public {
        require(msg.sender == owner, "Only owner can change the value");
        value = newValue;
    }
}