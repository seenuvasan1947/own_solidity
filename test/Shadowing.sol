pragma solidity ^0.4.0;

// Contract with shadowing issues - should be detected by SCWE-010 rule
contract ShadowingExample {
    uint public balance;
    uint public amount;
    address public owner;

    // Function parameter shadows state variable
    function deposit(uint balance) public {
        // Local variable 'balance' shadows the contract's balance variable
        balance += balance;  // This affects local 'balance', not state variable
    }
    
    // Function parameter shadows another state variable
    function withdraw(uint amount) public {
        // Parameter 'amount' shadows state variable 'amount'
        if (amount > balance) {
            revert("Insufficient balance");
        }
        balance -= amount;
    }
    
    // Local variable shadows state variable
    function processPayment() public {
        uint owner = 100;  // Local variable shadows state variable 'owner'
        uint balance = 50; // Local variable shadows state variable 'balance'
        
        // These local variables shadow the state variables
    }
    
    // Function name shadows state variable
    function balance() public view returns (uint) {
        // Function name 'balance' shadows state variable 'balance'
        return 0;
    }
    
    // Local variable shadows function parameter
    function transfer(uint value) public {
        uint value = value * 2;  // Local variable shadows parameter 'value'
        // This creates confusion
    }
}

// Contract without shadowing issues - should NOT be detected
contract NoShadowingExample {
    uint public balance;
    uint public amount;
    address public owner;

    // No shadowing - parameter has different name
    function deposit(uint depositAmount) public {
        balance += depositAmount;  // Clear and unambiguous
    }
    
    // No shadowing - parameter has different name
    function withdraw(uint withdrawAmount) public {
        if (withdrawAmount > balance) {
            revert("Insufficient balance");
        }
        balance -= withdrawAmount;
    }
    
    // No shadowing - local variables have different names
    function processPayment() public {
        uint paymentAmount = 100;  // Different name from state variables
        uint processingFee = 50;   // Different name from state variables
        
        // No confusion with state variables
    }
    
    // No shadowing - function has different name
    function getBalance() public view returns (uint) {
        return balance;  // Clear reference to state variable
    }
    
    // No shadowing - local variable has different name
    function transfer(uint value) public {
        uint doubledValue = value * 2;  // Different name from parameter
        // Clear and unambiguous
    }
}
