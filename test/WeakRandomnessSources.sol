// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// SCWE-024: Weak Randomness Sources Test Cases

// Vulnerable: Weak randomness using block variables
contract WeakRandomness {
    address public owner;
    uint public randomSeed;

    constructor() {
        owner = msg.sender;
    }

    // Vulnerable: Generate random number using block.timestamp
    function generateRandomNumber() public view returns (uint) {
        return uint(keccak256(abi.encodePacked(block.timestamp, msg.sender)));
    }

    // Vulnerable: Generate random number using block.difficulty
    function generateRandomValue() public view returns (uint) {
        return uint(keccak256(abi.encodePacked(block.difficulty, block.timestamp)));
    }

    // Vulnerable: Generate random number using block.number
    function generateRandomSeed() public view returns (uint) {
        return uint(keccak256(abi.encodePacked(block.number, block.timestamp)));
    }

    // Vulnerable: Generate random number using blockhash
    function generateRandomHash() public view returns (uint) {
        return uint(keccak256(abi.encodePacked(blockhash(block.number - 1), block.timestamp)));
    }

    // Vulnerable: Generate random number using now
    function generateRandomNow() public view returns (uint) {
        return uint(keccak256(abi.encodePacked(now, msg.sender)));
    }

    // Vulnerable: Generate random number using multiple weak sources
    function generateRandomMultiple() public view returns (uint) {
        return uint(keccak256(abi.encodePacked(block.timestamp, block.difficulty, block.number, msg.sender)));
    }
}

// Secure: Using Chainlink VRF for randomness
contract SecureRandomness {
    address public owner;
    uint public randomResult;
    bytes32 internal keyHash;
    uint256 internal fee;

    constructor() {
        owner = msg.sender;
    }

    // Secure: Generate random number using Chainlink VRF
    function generateRandomNumber() public returns (bytes32 requestId) {
        // This would typically call Chainlink VRF
        // require(LINK.balanceOf(address(this)) >= fee, "Not enough LINK");
        // return requestRandomness(keyHash, fee);
        return keccak256(abi.encodePacked("secure_randomness"));
    }

    // Secure: Generate random number using external oracle
    function generateRandomValue() public returns (uint) {
        // This would typically call an external oracle
        return uint(keccak256(abi.encodePacked("external_oracle_randomness")));
    }

    // Secure: Generate random number using cryptographic entropy
    function generateRandomSeed() public returns (uint) {
        // This would typically use cryptographic entropy
        return uint(keccak256(abi.encodePacked("cryptographic_entropy")));
    }
}

// Mixed: Some functions with weak randomness, some with secure randomness
contract MixedRandomness {
    address public owner;
    uint public randomSeed;

    constructor() {
        owner = msg.sender;
    }

    // Vulnerable: Function with weak randomness
    function generateRandomNumber() public view returns (uint) {
        return uint(keccak256(abi.encodePacked(block.timestamp, msg.sender)));
    }

    // Secure: Function with secure randomness
    function generateSecureRandom() public returns (uint) {
        // This would typically use Chainlink VRF or external oracle
        return uint(keccak256(abi.encodePacked("secure_randomness")));
    }

    // Vulnerable: Function with weak randomness
    function generateRandomValue() public view returns (uint) {
        return uint(keccak256(abi.encodePacked(block.difficulty, block.timestamp)));
    }
}

// Functions that don't generate randomness (should not be flagged)
contract NonRandomnessFunctions {
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
