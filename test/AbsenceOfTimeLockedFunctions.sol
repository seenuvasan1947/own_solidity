// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// SCWE-020: Absence of Time-Locked Functions Test Cases

// Vulnerable: No time-lock mechanisms
contract NoTimeLock {
    address public owner;
    uint public funds;

    constructor() {
        owner = msg.sender;
        funds = 1000;
    }

    // Vulnerable: Critical function without time-lock
    function withdrawFunds(uint amount) public {
        require(msg.sender == owner, "Not the owner");
        funds -= amount;
    }

    // Vulnerable: Critical function without time-lock
    function transferOwnership(address newOwner) public {
        require(msg.sender == owner, "Not the owner");
        owner = newOwner;
    }

    // Vulnerable: Critical function without time-lock
    function emergencyWithdraw() public {
        require(msg.sender == owner, "Not the owner");
        funds = 0;
    }
}

// Secure: Time-locked functions
contract TimeLockExample {
    address public owner;
    uint public funds;
    uint public lastWithdrawalTime;
    uint public withdrawalDelay = 1 weeks;

    constructor() {
        owner = msg.sender;
        funds = 1000;
        lastWithdrawalTime = block.timestamp;
    }

    // Secure: Critical function with time-lock
    function withdrawFunds(uint amount) public {
        require(msg.sender == owner, "Not the owner");
        require(block.timestamp >= lastWithdrawalTime + withdrawalDelay, "Time lock not expired");
        
        lastWithdrawalTime = block.timestamp;
        funds -= amount;
    }

    // Secure: Critical function with time-lock
    function transferOwnership(address newOwner) public {
        require(msg.sender == owner, "Not the owner");
        require(block.timestamp >= lastWithdrawalTime + withdrawalDelay, "Time lock not expired");
        
        lastWithdrawalTime = block.timestamp;
        owner = newOwner;
    }
}

// Mixed: Some functions with time-lock, some without
contract MixedTimeLock {
    address public owner;
    uint public funds;
    uint public lastExecutionTime;
    uint public executionDelay = 1 days;

    constructor() {
        owner = msg.sender;
        funds = 1000;
        lastExecutionTime = block.timestamp;
    }

    // Secure: Function with time-lock
    function withdrawFunds(uint amount) public {
        require(msg.sender == owner, "Not the owner");
        require(block.timestamp >= lastExecutionTime + executionDelay, "Time lock not expired");
        
        lastExecutionTime = block.timestamp;
        funds -= amount;
    }

    // Vulnerable: Function without time-lock
    function emergencyWithdraw() public {
        require(msg.sender == owner, "Not the owner");
        funds = 0;
    }

    // Secure: Function with time-lock using block.number
    function updateDelay(uint newDelay) public {
        require(msg.sender == owner, "Not the owner");
        require(block.number >= lastExecutionTime + executionDelay, "Time lock not expired");
        
        lastExecutionTime = block.number;
        executionDelay = newDelay;
    }
}

// Advanced time-lock implementation
contract AdvancedTimeLock {
    address public owner;
    uint public funds;
    mapping(bytes32 => uint) public timelock;
    uint public constant TIMELOCK_DELAY = 2 days;

    constructor() {
        owner = msg.sender;
        funds = 1000;
    }

    // Secure: Function with advanced time-lock
    function withdrawFunds(uint amount) public {
        require(msg.sender == owner, "Not the owner");
        
        bytes32 txHash = keccak256(abi.encodePacked("withdraw", amount, block.timestamp));
        require(block.timestamp >= timelock[txHash] + TIMELOCK_DELAY, "Time lock not expired");
        
        timelock[txHash] = block.timestamp;
        funds -= amount;
    }

    // Secure: Function with time-lock check
    function transferOwnership(address newOwner) public {
        require(msg.sender == owner, "Not the owner");
        
        bytes32 txHash = keccak256(abi.encodePacked("transferOwnership", newOwner, block.timestamp));
        require(block.timestamp >= timelock[txHash] + TIMELOCK_DELAY, "Time lock not expired");
        
        timelock[txHash] = block.timestamp;
        owner = newOwner;
    }
}

// Functions that don't need time-locks (should not be flagged)
contract NonCriticalFunctions {
    address public owner;
    uint public balance;

    constructor() {
        owner = msg.sender;
    }

    function deposit() public payable {
        balance += msg.value;
    }

    function getBalance() public view returns (uint) {
        return balance;
    }

    function isOwner() public view returns (bool) {
        return msg.sender == owner;
    }

    function getOwner() public view returns (address) {
        return owner;
    }
}
