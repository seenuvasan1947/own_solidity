// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// SCWE-026: Insufficient Hash Verification Test Cases

// Vulnerable: No hash verification
contract InsufficientHashVerification {
    address public owner;
    mapping(bytes32 => bool) public processedHashes;

    constructor() {
        owner = msg.sender;
    }

    // Vulnerable: Process hash without verification
    function processHash(bytes32 hash) public {
        // Process hash without verification
        processedHashes[hash] = true;
    }

    // Vulnerable: Handle message hash without verification
    function handleMessageHash(bytes32 messageHash) public {
        // Handle message hash without verification
        processedHashes[messageHash] = true;
    }

    // Vulnerable: Execute transaction hash without verification
    function executeTransactionHash(bytes32 transactionHash) public {
        // Execute transaction hash without verification
        processedHashes[transactionHash] = true;
    }

    // Vulnerable: Process data hash without verification
    function processDataHash(bytes32 dataHash) public {
        // Process data hash without verification
        processedHashes[dataHash] = true;
    }
}

// Secure: Sufficient hash verification
contract SufficientHashVerification {
    address public owner;
    mapping(bytes32 => bool) public processedHashes;

    constructor() {
        owner = msg.sender;
    }

    // Secure: Process hash with verification
    function processHash(bytes32 hash, bytes memory data) public {
        require(keccak256(data) == hash, "Invalid hash");
        processedHashes[hash] = true;
    }

    // Secure: Handle message hash with verification
    function handleMessageHash(bytes32 messageHash, bytes memory message) public {
        require(keccak256(message) == messageHash, "Invalid message hash");
        processedHashes[messageHash] = true;
    }

    // Secure: Execute transaction hash with verification
    function executeTransactionHash(bytes32 transactionHash, bytes memory transaction) public {
        require(keccak256(transaction) == transactionHash, "Invalid transaction hash");
        processedHashes[transactionHash] = true;
    }

    // Secure: Process data hash with verification
    function processDataHash(bytes32 dataHash, bytes memory data) public {
        require(keccak256(data) == dataHash, "Invalid data hash");
        processedHashes[dataHash] = true;
    }
}

// Secure: Hash verification with multiple checks
contract AdvancedHashVerification {
    address public owner;
    mapping(bytes32 => bool) public processedHashes;
    mapping(bytes32 => uint) public hashTimestamps;

    constructor() {
        owner = msg.sender;
    }

    // Secure: Process hash with multiple verification checks
    function processHash(bytes32 hash, bytes memory data, uint timestamp) public {
        require(keccak256(data) == hash, "Invalid hash");
        require(block.timestamp <= timestamp + 1 hours, "Hash expired");
        require(!processedHashes[hash], "Hash already processed");
        processedHashes[hash] = true;
        hashTimestamps[hash] = block.timestamp;
    }

    // Secure: Handle message hash with integrity check
    function handleMessageHash(bytes32 messageHash, bytes memory message) public {
        require(keccak256(message) == messageHash, "Invalid message hash");
        require(!processedHashes[messageHash], "Message hash already processed");
        processedHashes[messageHash] = true;
    }

    // Secure: Execute transaction hash with authenticity check
    function executeTransactionHash(bytes32 transactionHash, bytes memory transaction) public {
        require(keccak256(transaction) == transactionHash, "Invalid transaction hash");
        require(!processedHashes[transactionHash], "Transaction hash already processed");
        processedHashes[transactionHash] = true;
    }
}

// Mixed: Some functions with hash verification, some without
contract MixedHashVerification {
    address public owner;
    mapping(bytes32 => bool) public processedHashes;

    constructor() {
        owner = msg.sender;
    }

    // Secure: Function with hash verification
    function processHash(bytes32 hash, bytes memory data) public {
        require(keccak256(data) == hash, "Invalid hash");
        processedHashes[hash] = true;
    }

    // Vulnerable: Function without hash verification
    function handleMessageHash(bytes32 messageHash) public {
        // Handle message hash without verification
        processedHashes[messageHash] = true;
    }

    // Secure: Function with hash verification
    function executeTransactionHash(bytes32 transactionHash, bytes memory transaction) public {
        require(keccak256(transaction) == transactionHash, "Invalid transaction hash");
        processedHashes[transactionHash] = true;
    }
}

// Functions that don't process hashes (should not be flagged)
contract NonHashFunctions {
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
