// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// SCWE-019: Insecure Signature Verification Test Cases

// Vulnerable: Missing signature validation
contract InsecureSignatureExample {
    address public owner;

    constructor() {
        owner = msg.sender;
    }

    // Vulnerable: ecrecover without proper validation
    function executeTransaction(bytes32 hash, uint8 v, bytes32 r, bytes32 s) public {
        address signer = ecrecover(hash, v, r, s);
        if (signer == owner) {
            // Execute some sensitive action without proper validation
        }
    }

    // Vulnerable: ecrecover assignment without validation
    function processTransaction(bytes32 hash, uint8 v, bytes32 r, bytes32 s) public {
        address signer = ecrecover(hash, v, r, s);
        // Missing validation before proceeding
    }

    // Vulnerable: ecrecover in require but not properly validated
    function verifyTransaction(bytes32 hash, uint8 v, bytes32 r, bytes32 s) public {
        address signer = ecrecover(hash, v, r, s);
        require(signer != address(0), "Invalid signature");
        // Missing check for expected signer
    }
}

// Secure: Proper signature validation
contract SecureSignatureExample {
    address public owner;

    constructor() {
        owner = msg.sender;
    }

    // Secure: Proper signature validation with require
    function executeTransaction(bytes32 hash, uint8 v, bytes32 r, bytes32 s) public {
        address signer = ecrecover(hash, v, r, s);
        require(signer == owner, "Invalid signature");
        // Execute some sensitive action
    }

    // Secure: Proper signature validation with assert
    function processTransaction(bytes32 hash, uint8 v, bytes32 r, bytes32 s) public {
        address signer = ecrecover(hash, v, r, s);
        assert(signer == owner);
        // Process transaction
    }

    // Secure: Proper signature validation with if statement
    function verifyTransaction(bytes32 hash, uint8 v, bytes32 r, bytes32 s) public {
        address signer = ecrecover(hash, v, r, s);
        if (signer == owner) {
            // Process transaction
        } else {
            revert("Invalid signature");
        }
    }
}

// Mixed: Some secure, some vulnerable
contract MixedSignatureExample {
    address public owner;
    mapping(address => bool) public authorized;

    constructor() {
        owner = msg.sender;
        authorized[msg.sender] = true;
    }

    // Secure: Proper validation
    function executeTransaction(bytes32 hash, uint8 v, bytes32 r, bytes32 s) public {
        address signer = ecrecover(hash, v, r, s);
        require(signer == owner, "Invalid signature");
        // Execute transaction
    }

    // Vulnerable: Missing validation
    function processTransaction(bytes32 hash, uint8 v, bytes32 r, bytes32 s) public {
        address signer = ecrecover(hash, v, r, s);
        // Missing validation
    }

    // Secure: Multiple validation checks
    function validateTransaction(bytes32 hash, uint8 v, bytes32 r, bytes32 s) public {
        address signer = ecrecover(hash, v, r, s);
        require(signer != address(0), "Invalid signature");
        require(signer == owner || authorized[signer], "Unauthorized signer");
        // Process transaction
    }
}

// Non-signature functions (should not be flagged)
contract NonSignatureContract {
    address public owner;
    uint public balance;

    constructor() {
        owner = msg.sender;
    }

    function deposit() public payable {
        balance += msg.value;
    }

    function withdraw(uint amount) public {
        require(msg.sender == owner, "Not authorized");
        balance -= amount;
        payable(msg.sender).transfer(amount);
    }

    function getBalance() public view returns (uint) {
        return balance;
    }
}
