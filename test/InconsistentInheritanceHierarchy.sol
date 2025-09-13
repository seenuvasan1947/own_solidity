pragma solidity ^0.4.0;

// Parent contracts with conflicting functions and variables
contract ParentA {
    uint public value;
    string public name;

    function setValue(uint _value) public {
        value = _value;
    }
    
    function getName() public view returns (string) {
        return name;
    }
}

contract ParentB {
    uint public value;  // Conflicting variable with ParentA
    uint public count;

    function setValue(uint _value) public {  // Conflicting function with ParentA
        value = _value * 2;
    }
    
    function getCount() public view returns (uint) {
        return count;
    }
}

contract ParentC {
    uint public value;  // Another conflicting variable
    bool public active;

    function setValue(uint _value) public {  // Another conflicting function
        value = _value + 10;
    }
}

// Vulnerable: Multiple inheritance with diamond problem
contract VulnerableChild is ParentA, ParentB, ParentC {
    // Ambiguous: which setValue should be called?
    function setValue(uint _value) public {
        // No explicit parent call - should be detected
    }
    
    // Ambiguous: which value variable is being accessed?
    function getValue() public view returns (uint) {
        return value;  // Which parent's value?
    }
}

// Vulnerable: Conflicting variable types
contract ConflictingTypes is ParentA {
    uint public value;  // Conflicting with ParentA's value
    
    function setValue(uint _value) public {
        value = _value;
    }
}

// Secure: Single inheritance with explicit overrides
contract SecureChild is ParentA {
    function setValue(uint _value) public {
        ParentA.setValue(_value);  // Explicit parent call
    }
    
    function getValue() public view returns (uint) {
        return ParentA.value;  // Explicit parent variable access
    }
}

// Secure: Multiple inheritance with explicit resolution
contract SecureMultipleInheritance is ParentA, ParentB {
    function setValue(uint _value) public {
        ParentA.setValue(_value);  // Explicit parent call
    }
    
    function setValueB(uint _value) public {
        ParentB.setValue(_value);  // Explicit parent call
    }
}
