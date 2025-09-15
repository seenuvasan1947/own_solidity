// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// SCWE-025: Improper Cryptographic Key Management Test Cases

// Vulnerable: Hardcoded cryptographic keys
contract ImproperKeyManagement {
    address public owner;
    bytes32 private key;
    bytes32 private secret;
    bytes32 private seed;

    constructor() {
        owner = msg.sender;
        // Vulnerable: Hardcoded cryptographic key
        key = keccak256("insecure-key");
        // Vulnerable: Hardcoded secret
        secret = keccak256("my-secret");
        // Vulnerable: Hardcoded seed
        seed = keccak256("random-seed");
    }

    // Vulnerable: Function with hardcoded key
    function generateHash() public view returns (bytes32) {
        return keccak256("hardcoded-hash");
    }

    // Vulnerable: Function with hardcoded secret
    function generateSecret() public view returns (bytes32) {
        return keccak256("my-secret-key");
    }

    // Vulnerable: Function with hardcoded seed
    function generateSeed() public view returns (bytes32) {
        return keccak256("random-seed-value");
    }
}

// Secure: Proper key management with constructor parameters
contract ProperKeyManagement {
    address public owner;
    bytes32 private key;
    bytes32 private secret;
    bytes32 private seed;

    constructor(bytes32 _key, bytes32 _secret, bytes32 _seed) {
        owner = msg.sender;
        // Secure: Key passed as constructor parameter
        key = _key;
        // Secure: Secret passed as constructor parameter
        secret = _secret;
        // Secure: Seed passed as constructor parameter
        seed = _seed;
    }

    // Secure: Function that updates key
    function updateKey(bytes32 _newKey) public {
        require(msg.sender == owner, "Not authorized");
        key = _newKey;
    }

    // Secure: Function that rotates secret
    function rotateSecret(bytes32 _newSecret) public {
        require(msg.sender == owner, "Not authorized");
        secret = _newSecret;
    }

    // Secure: Function that generates new seed
    function generateNewSeed() public {
        require(msg.sender == owner, "Not authorized");
        seed = keccak256(abi.encodePacked(block.timestamp, msg.sender, secret));
    }
}

// Secure: Using external randomness for key generation
contract SecureKeyManagement {
    address public owner;
    bytes32 private key;
    bytes32 private secret;

    constructor() {
        owner = msg.sender;
        // Secure: Generate key using external randomness
        key = keccak256(abi.encodePacked("external_randomness_source"));
        // Secure: Generate secret using external randomness
        secret = keccak256(abi.encodePacked("external_secret_source"));
    }

    // Secure: Function that generates key using external oracle
    function generateKeyFromOracle() public returns (bytes32) {
        require(msg.sender == owner, "Not authorized");
        // This would typically call an external oracle
        return keccak256(abi.encodePacked("oracle_randomness"));
    }

    // Secure: Function that generates secret using Chainlink VRF
    function generateSecretFromVRF() public returns (bytes32) {
        require(msg.sender == owner, "Not authorized");
        // This would typically call Chainlink VRF
        return keccak256(abi.encodePacked("vrf_randomness"));
    }
}

// Mixed: Some functions with hardcoded keys, some with secure key management
contract MixedKeyManagement {
    address public owner;
    bytes32 private key;
    bytes32 private secret;

    constructor(bytes32 _key) {
        owner = msg.sender;
        // Secure: Key passed as constructor parameter
        key = _key;
        // Vulnerable: Hardcoded secret
        secret = keccak256("hardcoded-secret");
    }

    // Vulnerable: Function with hardcoded key
    function generateHash() public view returns (bytes32) {
        return keccak256("hardcoded-hash");
    }

    // Secure: Function that updates key
    function updateKey(bytes32 _newKey) public {
        require(msg.sender == owner, "Not authorized");
        key = _newKey;
    }

    // Secure: Function that generates new secret
    function generateNewSecret() public {
        require(msg.sender == owner, "Not authorized");
        secret = keccak256(abi.encodePacked(block.timestamp, msg.sender, key));
    }
}

// Functions that don't handle cryptographic keys (should not be flagged)
contract NonKeyFunctions {
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
