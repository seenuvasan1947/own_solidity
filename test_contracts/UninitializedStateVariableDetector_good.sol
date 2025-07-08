pragma solidity ^0.8.0;

contract InitializedGood {
    // All state variables are explicitly initialized at their declaration.
    uint public initializedUint = 1;
    address private initializedAddress = address(0x123);
    bool public initializedBool = true;
    string internal initializedString = "Hello, world!";
    bytes initializedBytes = hex"deadbeef";
    int256 initializedInt = -100;

    // Variables initialized at declaration, and then potentially updated in the constructor.
    // This explicitly assigns a starting value, satisfying the rule.
    uint public valueSetInConstructor = 0; // Explicitly initialized to 0
    address public owner = address(0);     // Explicitly initialized to address(0)

    constructor() {
        // Further assignments in the constructor are fine and do not affect the rule's detection
        // if the variable was already initialized at declaration.
        valueSetInConstructor = 456;
        owner = msg.sender;
    }

    function getInitializedUint() public view returns (uint) {
        return initializedUint;
    }

    function getOwner() public view returns (address) {
        return owner;
    }
}