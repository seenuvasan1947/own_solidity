// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// Test contract for SCWE-034: Insecure Cross-Chain Messaging
// This contract demonstrates vulnerable patterns in cross-chain message handling

contract InsecureCrossChain {
    event MessageProcessed(bytes message);

    // Vulnerable: No validation of the sender (anyone can call this function!)
    // No signature verification (attackers can inject fake messages!)
    // No relayer authorization
    // No replay protection
    function processMessage(bytes memory message) public {
        emit MessageProcessed(message);
        // Process message without any security checks
    }
    
    // Vulnerable: Cross-chain bridge without proper validation
    function bridgeMessage(address target, bytes memory data) public {
        // No relayer validation - anyone can call
        // No signature verification - fake messages possible
        // No replay protection - same message can be processed multiple times
        (bool success,) = target.call(data);
        require(success, "Bridge call failed");
    }
    
    // Vulnerable: Message relay without security measures
    function relayMessage(bytes memory payload) public {
        // Missing all security validations
        // Vulnerable to unauthorized relayers
        // Vulnerable to message replay attacks
        // Vulnerable to signature forgery
    }
}

contract SecureCrossChain {
    mapping(address => bool) public trustedRelayers;
    mapping(bytes32 => bool) public processedMessages;

    event MessageProcessed(bytes32 indexed messageHash, address indexed sender);
    event RelayerUpdated(address relayer, bool status);

    address public owner;

    modifier onlyOwner() {
        require(msg.sender == owner, "Not the owner");
        _;
    }

    constructor(address[] memory initialRelayers) {
        owner = msg.sender;
        for (uint i = 0; i < initialRelayers.length; i++) {
            trustedRelayers[initialRelayers[i]] = true;
        }
    }

    function setRelayer(address relayer, bool status) external onlyOwner {
        trustedRelayers[relayer] = status;
        emit RelayerUpdated(relayer, status);
    }

    function processMessage(
        bytes memory message, 
        uint8 v, bytes32 r, bytes32 s
    ) public {
        // Relayer authorization check
        require(trustedRelayers[msg.sender], "Unauthorized relayer");

        // Signature verification
        bytes32 messageHash = keccak256(abi.encodePacked("\x19Ethereum Signed Message:\n32", keccak256(message)));
        address signer = ecrecover(messageHash, v, r, s);
        require(signer != address(0), "Invalid signature");

        // Replay protection
        require(!processedMessages[messageHash], "Message already processed");
        processedMessages[messageHash] = true;

        emit MessageProcessed(messageHash, signer);
        // Securely process the message
    }
    
    function bridgeMessageSecure(
        address target, 
        bytes memory data,
        uint8 v, bytes32 r, bytes32 s
    ) public {
        require(trustedRelayers[msg.sender], "Unauthorized relayer");
        
        bytes32 dataHash = keccak256(data);
        address signer = ecrecover(dataHash, v, r, s);
        require(signer != address(0), "Invalid signature");
        
        require(!processedMessages[dataHash], "Data already processed");
        processedMessages[dataHash] = true;
        
        (bool success,) = target.call(data);
        require(success, "Secure bridge call failed");
    }
}
