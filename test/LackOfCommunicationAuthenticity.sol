// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// SCWE-023: Lack of Communication Authenticity Test Cases

// Vulnerable: No authenticity verification
contract NoAuthenticity {
    address public owner;
    mapping(address => uint) public balances;

    constructor() {
        owner = msg.sender;
    }

    // Vulnerable: Process message without authenticity check
    function processMessage(bytes memory message) public {
        // Process message without authenticity check
        balances[msg.sender] += 100;
    }

    // Vulnerable: Handle transaction without authenticity check
    function handleTransaction(bytes memory data) public {
        // Handle transaction without authenticity check
        balances[msg.sender] += 50;
    }

    // Vulnerable: Execute action without authenticity check
    function executeAction(bytes memory action) public {
        // Execute action without authenticity check
        balances[msg.sender] += 25;
    }
}

// Secure: Authentic communication with signatures
contract AuthenticCommunication {
    address public owner;
    mapping(address => uint) public balances;

    constructor() {
        owner = msg.sender;
    }

    // Secure: Process message with signature verification
    function processMessage(bytes memory message, bytes memory signature) public {
        bytes32 messageHash = keccak256(message);
        address signer = ecrecover(messageHash, signature);
        require(signer == msg.sender, "Invalid signature");
        balances[msg.sender] += 100;
    }

    // Secure: Handle transaction with signature verification
    function handleTransaction(bytes memory data, bytes memory signature) public {
        bytes32 txHash = keccak256(data);
        address signer = ecrecover(txHash, signature);
        require(signer == msg.sender, "Invalid signature");
        balances[msg.sender] += 50;
    }

    // Secure: Execute action with signature verification
    function executeAction(bytes memory action, bytes memory signature) public {
        bytes32 actionHash = keccak256(action);
        address signer = ecrecover(actionHash, signature);
        require(signer == msg.sender, "Invalid signature");
        balances[msg.sender] += 25;
    }
}

// Secure: Authentic communication with ECDSA
contract ECDSAAuthenticCommunication {
    address public owner;
    mapping(address => uint) public balances;

    constructor() {
        owner = msg.sender;
    }

    // Secure: Process message with ECDSA signature verification
    function processMessage(bytes memory message, uint8 v, bytes32 r, bytes32 s) public {
        bytes32 messageHash = keccak256(message);
        address signer = ecrecover(messageHash, v, r, s);
        require(signer == msg.sender, "Invalid signature");
        balances[msg.sender] += 100;
    }

    // Secure: Handle transaction with ECDSA signature verification
    function handleTransaction(bytes memory data, uint8 v, bytes32 r, bytes32 s) public {
        bytes32 txHash = keccak256(data);
        address signer = ecrecover(txHash, v, r, s);
        require(signer == msg.sender, "Invalid signature");
        balances[msg.sender] += 50;
    }

    // Secure: Execute action with ECDSA signature verification
    function executeAction(bytes memory action, uint8 v, bytes32 r, bytes32 s) public {
        bytes32 actionHash = keccak256(action);
        address signer = ecrecover(actionHash, v, r, s);
        require(signer == msg.sender, "Invalid signature");
        balances[msg.sender] += 25;
    }
}

// Mixed: Some functions with authenticity verification, some without
contract MixedAuthenticity {
    address public owner;
    mapping(address => uint) public balances;

    constructor() {
        owner = msg.sender;
    }

    // Secure: Function with authenticity verification
    function processMessage(bytes memory message, bytes memory signature) public {
        bytes32 messageHash = keccak256(message);
        address signer = ecrecover(messageHash, signature);
        require(signer == msg.sender, "Invalid signature");
        balances[msg.sender] += 100;
    }

    // Vulnerable: Function without authenticity verification
    function handleTransaction(bytes memory data) public {
        // Handle transaction without authenticity verification
        balances[msg.sender] += 50;
    }

    // Secure: Function with authenticity verification
    function executeAction(bytes memory action, bytes memory signature) public {
        bytes32 actionHash = keccak256(action);
        address signer = ecrecover(actionHash, signature);
        require(signer == msg.sender, "Invalid signature");
        balances[msg.sender] += 25;
    }
}

// Functions that don't need authenticity verification (should not be flagged)
contract NonMessageFunctions {
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

    function isOwner() public view returns (bool) {
        return msg.sender == owner;
    }
}
