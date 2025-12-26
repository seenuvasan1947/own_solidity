// SPDX-License-Identifier: MIT
pragma solidity ^0.4.20;  // Old version for testing

// Test contract for compiler bug detectors

// S-BUG-002: Enum conversion
contract EnumTest {
    enum Status { Pending, Active, Closed }
    
    function setStatus(uint value) public returns (Status) {
        return Status(value);  // Dangerous in old Solidity versions
    }
}

// S-BUG-001: Multiple constructors
contract MultipleConstructors {
    uint public x;
    
    // New-style constructor
    constructor() public {
        x = 0;
    }
    
    // Old-style constructor (same name as contract)
    function MultipleConstructors() public {
        x = 1;
    }
}

// S-BUG-003: Storage signed integer array
contract SignedArrayBug {
    int[3] balances;  // Storage signed integer array
    
    function setBal() public {
        balances = [-1, -1, -1];  // Problematic in 0.4.7-0.5.9
    }
}

// GOOD: No issues
contract GoodContract {
    uint[] public values;
    
    constructor() public {
        values.push(1);
    }
}
