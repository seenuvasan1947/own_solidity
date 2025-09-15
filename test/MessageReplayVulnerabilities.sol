// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// SCWE-022: Message Replay Vulnerabilities Test Cases

// Vulnerable: No replay protection
contract ReplayVulnerable {
    address public owner;
    mapping(address => uint) public balances;

    constructor() {
        owner = msg.sender;
    }

    // Vulnerable: Process message without replay protection
    function processMessage(bytes memory message) public {
        // Process message without replay protection
        balances[msg.sender] += 100;
    }

    // Vulnerable: Handle transaction without replay protection
    function handleTransaction(bytes memory data) public {
        // Handle transaction without replay protection
        balances[msg.sender] += 50;
    }

    // Vulnerable: Execute action without replay protection
    function executeAction(bytes memory action) public {
        // Execute action without replay protection
        balances[msg.sender] += 25;
    }
}

// Secure: Replay protection with nonces
contract ReplayProtected {
    address public owner;
    mapping(address => uint) public balances;
    mapping(bytes32 => bool) public usedMessages;
    mapping(address => uint) public nonces;

    constructor() {
        owner = msg.sender;
    }

    // Secure: Process message with nonce protection
    function processMessage(bytes memory message, uint nonce) public {
        bytes32 messageHash = keccak256(abi.encodePacked(message, nonce, msg.sender));
        require(!usedMessages[messageHash], "Message already used");
        usedMessages[messageHash] = true;
        nonces[msg.sender] = nonce;
        balances[msg.sender] += 100;
    }

    // Secure: Handle transaction with nonce protection
    function handleTransaction(bytes memory data, uint nonce) public {
        bytes32 txHash = keccak256(abi.encodePacked(data, nonce, msg.sender));
        require(!usedMessages[txHash], "Transaction already used");
        usedMessages[txHash] = true;
        nonces[msg.sender] = nonce;
        balances[msg.sender] += 50;
    }

    // Secure: Execute action with nonce protection
    function executeAction(bytes memory action, uint nonce) public {
        bytes32 actionHash = keccak256(abi.encodePacked(action, nonce, msg.sender));
        require(!usedMessages[actionHash], "Action already used");
        usedMessages[actionHash] = true;
        nonces[msg.sender] = nonce;
        balances[msg.sender] += 25;
    }
}

// Secure: Replay protection with timestamps
contract TimestampReplayProtected {
    address public owner;
    mapping(address => uint) public balances;
    mapping(bytes32 => bool) public usedMessages;
    uint public constant MESSAGE_VALIDITY = 1 hours;

    constructor() {
        owner = msg.sender;
    }

    // Secure: Process message with timestamp protection
    function processMessage(bytes memory message, uint timestamp) public {
        require(block.timestamp <= timestamp + MESSAGE_VALIDITY, "Message expired");
        bytes32 messageHash = keccak256(abi.encodePacked(message, timestamp, msg.sender));
        require(!usedMessages[messageHash], "Message already used");
        usedMessages[messageHash] = true;
        balances[msg.sender] += 100;
    }

    // Secure: Handle transaction with timestamp protection
    function handleTransaction(bytes memory data, uint timestamp) public {
        require(block.timestamp <= timestamp + MESSAGE_VALIDITY, "Transaction expired");
        bytes32 txHash = keccak256(abi.encodePacked(data, timestamp, msg.sender));
        require(!usedMessages[txHash], "Transaction already used");
        usedMessages[txHash] = true;
        balances[msg.sender] += 50;
    }
}

// Mixed: Some functions with replay protection, some without
contract MixedReplayProtection {
    address public owner;
    mapping(address => uint) public balances;
    mapping(bytes32 => bool) public usedMessages;
    mapping(address => uint) public nonces;

    constructor() {
        owner = msg.sender;
    }

    // Secure: Function with replay protection
    function processMessage(bytes memory message, uint nonce) public {
        bytes32 messageHash = keccak256(abi.encodePacked(message, nonce, msg.sender));
        require(!usedMessages[messageHash], "Message already used");
        usedMessages[messageHash] = true;
        nonces[msg.sender] = nonce;
        balances[msg.sender] += 100;
    }

    // Vulnerable: Function without replay protection
    function handleTransaction(bytes memory data) public {
        // Handle transaction without replay protection
        balances[msg.sender] += 50;
    }

    // Secure: Function with replay protection
    function executeAction(bytes memory action, uint nonce) public {
        bytes32 actionHash = keccak256(abi.encodePacked(action, nonce, msg.sender));
        require(!usedMessages[actionHash], "Action already used");
        usedMessages[actionHash] = true;
        nonces[msg.sender] = nonce;
        balances[msg.sender] += 25;
    }
}

// Functions that don't need replay protection (should not be flagged)
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
