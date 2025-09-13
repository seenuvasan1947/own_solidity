pragma solidity ^0.4.0;

// Contract with unused variables - should be detected by SCWE-007 rule
contract UnusedVariables {
    uint public balance;
    uint public unusedStateVariable;  // Unused state variable
    string private unusedString;      // Unused private variable
    address internal unusedAddress;   // Unused internal variable
    bool public usedVariable;         // Used variable (should not be detected)

    function deposit(uint amount) public {
        balance += amount;
        usedVariable = true;  // Using the variable
    }
    
    function withdraw(uint amount) public {
        balance -= amount;
    }
    
    function processData(uint data) public {
        uint unusedLocalVar = data * 2;  // Unused local variable
        uint usedLocalVar = data + 1;    // Used local variable
        
        balance += usedLocalVar;  // Using the local variable
        
        // unusedLocalVar is never used
    }
    
    function anotherFunction() public {
        string memory unusedMemoryVar = "test";  // Unused memory variable
        uint temp = 100;
        
        balance += temp;  // temp is used, but unusedMemoryVar is not
    }
    
    function complexFunction(uint param1, uint param2) public {
        uint result1 = param1 * 2;  // Used
        uint result2 = param2 + 1;  // Unused
        uint result3 = param1 + param2;  // Used
        
        balance += result1 + result3;  // Using result1 and result3
        
        // result2 is never used
    }
}

// Contract without unused variables - should NOT be detected
contract NoUnusedVariables {
    uint public balance;
    uint public counter;
    string public name;

    function deposit(uint amount) public {
        balance += amount;
        counter++;
    }
    
    function withdraw(uint amount) public {
        balance -= amount;
        counter++;
    }
    
    function setName(string _name) public {
        name = _name;
    }
    
    function processData(uint data) public {
        uint processedData = data * 2;
        uint finalResult = processedData + 1;
        
        balance += finalResult;
    }
}
