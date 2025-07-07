pragma solidity ^0.8.0;

contract VulnerableContract {
    uint256 public value;
    bool public locked;

    constructor() {
        value = 100;
        locked = false;
    }

    function getValue() public view returns (uint256) {
        // Simulate some external interaction that can modify 'value'
        // but doesn't update 'locked' immediately.  This is the "stale" condition.
        return value;
    }

    function setValue(uint256 newValue) public {
        locked = true;
        value = newValue;
        locked = false;
    }

    // Attacker calls this, then rapidly calls getValue while locked=true,
    // getting a stale value.
    function attack(address attacker) public {
        setValue(200); // Simulate update to a new value.
        // Vulnerability: Attacker can read the wrong state during this window if the view function is called rapidly
    }
}