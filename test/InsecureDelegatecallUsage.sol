// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// Test contract for SCWE-035: Insecure Delegatecall Usage
// This contract demonstrates vulnerable patterns in delegatecall usage

contract InsecureDelegatecall {
    // Vulnerable: No validation, attacker-controlled contract can be used
    function executeDelegatecall(address target, bytes memory data) public {
        (bool success, ) = target.delegatecall(data);
        require(success, "Delegatecall failed");
        // Anyone can call executeDelegatecall() with a malicious contract
        // This will execute arbitrary code within the caller's context
        // Can lead to theft of funds, privilege escalation, or state corruption
    }
    
    // Vulnerable: Public function with user-controlled target
    function proxyCall(address implementation, bytes calldata data) external {
        (bool success, bytes memory result) = implementation.delegatecall(data);
        require(success, "Proxy call failed");
        // No access control - anyone can specify implementation
        // No target validation - malicious contracts can be used
    }
    
    // Vulnerable: Delegatecall without proper authorization
    function upgrade(address newImplementation, bytes memory initData) public {
        // Missing access control - anyone can upgrade
        (bool success, ) = newImplementation.delegatecall(initData);
        require(success, "Upgrade failed");
    }
}

contract SecureDelegatecall {
    address public owner;
    address public trustedTarget;
    mapping(address => bool) public trustedImplementations;

    modifier onlyOwner() {
        require(msg.sender == owner, "Not authorized");
        _;
    }

    constructor(address _trustedTarget) {
        owner = msg.sender;
        trustedTarget = _trustedTarget;
    }

    function updateTrustedTarget(address _newTarget) public onlyOwner {
        require(isTrusted(_newTarget), "Untrusted target");
        trustedTarget = _newTarget;
    }
    
    function addTrustedImplementation(address implementation) public onlyOwner {
        require(implementation != address(0), "Invalid address");
        trustedImplementations[implementation] = true;
    }
    
    function removeTrustedImplementation(address implementation) public onlyOwner {
        trustedImplementations[implementation] = false;
    }

    // Secure: Only owner can call, target is validated
    function executeDelegatecall(bytes memory data) public onlyOwner {
        require(trustedTarget != address(0), "Invalid target");
        (bool success, ) = trustedTarget.delegatecall(data);
        require(success, "Delegatecall failed");
    }
    
    // Secure: Access controlled and target validated
    function proxyCallSecure(address implementation, bytes calldata data) external onlyOwner {
        require(trustedImplementations[implementation], "Untrusted implementation");
        (bool success, bytes memory result) = implementation.delegatecall(data);
        require(success, "Secure proxy call failed");
    }
    
    // Secure: Proper access control and validation
    function upgradeSecure(address newImplementation, bytes memory initData) public onlyOwner {
        require(trustedImplementations[newImplementation], "Implementation not trusted");
        require(newImplementation != address(0), "Invalid implementation");
        
        (bool success, ) = newImplementation.delegatecall(initData);
        require(success, "Secure upgrade failed");
        
        // Update trusted target if needed
        trustedTarget = newImplementation;
    }

    function isTrusted(address _target) internal view returns (bool) {
        // Implement further checks if needed
        return _target != address(0) && trustedImplementations[_target];
    }
}

// Example of a malicious contract that could be used in attacks
contract MaliciousImplementation {
    address public owner;
    
    function maliciousFunction() external {
        // This would execute in the context of the calling contract
        // Could steal funds, change ownership, etc.
        owner = msg.sender; // This would overwrite the caller's owner variable
    }
}
