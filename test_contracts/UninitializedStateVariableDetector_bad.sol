pragma solidity ^0.8.0;

contract UninitializedBad {
    // These state variables are declared but not explicitly initialized.
    // They will default to their zero-equivalent values.
    uint public uninitializedUint;          // Defaults to 0
    address private uninitializedAddress;   // Defaults to address(0)
    bool public uninitializedBool;          // Defaults to false
    string internal uninitializedString;    // Defaults to empty string ("")
    bytes uninitializedBytes;               // Defaults to empty bytes (new bytes(0))
    int256 uninitializedInt;                // Defaults to 0

    // Even if assigned a value in the constructor, they are still "uninitialized" at declaration
    // according to this specific rule's logic (which checks for 'initialValue' at declaration).
    uint public valueSetInConstructor;
    address public owner;

    constructor() {
        // These assignments happen after the variable's declaration and initial default value assignment.
        valueSetInConstructor = 123;
        owner = msg.sender;
    }

    function getUninitializedUint() public view returns (uint) {
        return uninitializedUint;
    }

    function getUninitializedAddress() public view returns (address) {
        return uninitializedAddress;
    }
}