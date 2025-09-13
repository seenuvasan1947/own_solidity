---
title: Insecure Cross-Chain Messaging
id: SCWE-034
alias: insecure-cross-chain-messaging
platform: []
profiles: [L1]
mappings:
  scsvs-cg: [SCSVS-BRIDGE]
  scsvs-scg: [SCSVS-BRIDGE-2]
  cwe: [20]
status: new
---

## Relationships
- CWE-20: Improper Input Validation  
  [CWE-20 Link](https://cwe.mitre.org/data/definitions/20.html)

## Description  
Insecure cross-chain messaging refers to vulnerabilities that arise when communicating between different blockchains. This can lead to:
- Unauthorized actions by malicious actors.
- Loss of funds or data.
- Exploitation of vulnerabilities in cross-chain logic.

## Remediation
- **Validate messages:** Ensure all cross-chain messages are properly validated.
- **Use secure protocols:** Leverage secure cross-chain communication protocols.
- **Test thoroughly:** Conduct extensive testing to ensure cross-chain logic is secure.

## Examples
- **Insecure Cross-Chain Messaging**
    ```solidity
    pragma solidity ^0.8.0;

    contract InsecureCrossChain {
        event MessageProcessed(bytes message);

        function processMessage(bytes memory message) public {
            // ❌ No validation of the sender (anyone can call this function!)
            // ❌ No signature verification (attackers can inject fake messages!)
            // 🚨 No relayer authorization
            // 🚨 No replay protection
            emit MessageProcessed(message);
        }
    }
    ```
🔴 Issue: The function accepts messages without validation, allowing unauthorized transactions.

Unauthorized Relayers (Anyone Can Call!)
- Issue: The function allows any msg.sender to call processMessage(), meaning an attacker can send arbitrary messages.
- Impact: Attackers can forge transactions, trigger unintended actions, or drain funds if the function is connected to cross-chain asset transfers.

No Signature Verification (Fake Messages)
- Issue: The contract doesn’t verify the authenticity of the message.
- Impact: Attackers can inject fake messages and trick the contract into executing unauthorized actions.

Replay Attacks
- Issue: The contract doesn’t track processed messages.
- Impact: The same message can be replayed multiple times, leading to repeated execution of sensitive operations.

- **Secure Cross-Chain Messaging**
    ```solidity
    pragma solidity ^0.8.0;

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
            require(trustedRelayers[msg.sender], "Unauthorized relayer");

            bytes32 messageHash = keccak256(abi.encodePacked("\x19Ethereum Signed Message:\n32", keccak256(message)));
            address signer = ecrecover(messageHash, v, r, s);
            require(signer != address(0), "Invalid signature");

            require(!processedMessages[messageHash], "Message already processed");
            processedMessages[messageHash] = true;

            emit MessageProcessed(messageHash, signer);

            // ✅ Securely process the message
        }
    }
    ```

Fix: Implements signature verification, relayer validation, and replay protection.
Why is this better?
✅ Verifies Signatures Properly: Uses ecrecover() with Ethereum Signed Message hashing.
✅ Admin Can Manage Relayers: Allows dynamic relayer updates via setRelayer().
✅ Prevents Replay Attacks: Tracks processed messages in processedMessages mapping.
✅ Ensures Message Authenticity: Only validly signed messages are accepted.

---