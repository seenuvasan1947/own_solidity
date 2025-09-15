// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// Test contract for SCWE-033: Chain Split Risks
// This contract demonstrates vulnerable patterns that lack chain split protection

contract ChainSplitVulnerable {
    address public owner;
    mapping(address => uint256) public balances;
    
    constructor() {
        owner = msg.sender;
    }
    
    // Vulnerable: Cross-chain transaction processing without chain ID validation
    function processTransaction(bytes memory data) public {
        // Process transaction without chain split handling
        // This could lead to replay attacks across different chains
        require(msg.sender == owner, "Only owner can process");
        
        // Simulate processing without chain validation
        balances[msg.sender] += 100;
    }
    
    // Vulnerable: Bridge transfer without chain ID check
    function bridgeTransfer(address to, uint256 amount) public {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        balances[msg.sender] -= amount;
        balances[to] += amount;
        // Missing chain ID validation - vulnerable to chain split attacks
    }
    
    // Vulnerable: Cross-chain call without validation
    function crossChainCall(address target, bytes memory data) public {
        require(msg.sender == owner, "Only owner");
        (bool success,) = target.call(data);
        require(success, "Call failed");
        // No chain ID validation - could execute on wrong chain
    }
}

contract ChainSplitProtected {
    uint public chainId;
    address public owner;
    mapping(address => uint256) public balances;
    
    constructor(uint _chainId) {
        chainId = _chainId;
        owner = msg.sender;
    }
    
    // Protected: Includes chain ID validation
    function processTransaction(bytes memory data, uint transactionChainId) public {
        require(transactionChainId == chainId, "Invalid chain ID");
        require(msg.sender == owner, "Only owner can process");
        
        balances[msg.sender] += 100;
    }
    
    // Protected: Uses block.chainid for validation
    function bridgeTransferSecure(address to, uint256 amount) public {
        require(block.chainid == chainId, "Wrong chain");
        require(balances[msg.sender] >= amount, "Insufficient balance");
        balances[msg.sender] -= amount;
        balances[to] += amount;
    }
}
