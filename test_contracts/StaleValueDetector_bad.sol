pragma solidity ^0.8.0;

contract VulnerableContract {
    uint256 public value;
    address public owner;

    constructor() {
        owner = msg.sender;
        value = 10;
    }

    function getValue() public view returns (uint256) {
        // Simulate an external call that might change the state in another contract.
        // In a real-world scenario, this would be an actual external call.
        if (block.number % 2 == 0) {
            value = 20; // Simulate state change during the call.
        }
        return value; // Returns a potentially stale value.
    }

    function changeValue(uint256 newValue) public {
        require(msg.sender == owner, "Only owner can change the value");
        value = newValue;
    }
}