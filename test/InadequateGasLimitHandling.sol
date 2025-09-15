// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// Test contract for SCWE-036: Inadequate Gas Limit Handling
// This contract demonstrates vulnerable patterns in gas limit handling

contract InefficientProcessing {
    mapping(address => uint) public balances;
    address[] public users;
    
    // Vulnerable: Processes large arrays in a single transaction
    function batchTransfer(address[] memory recipients, uint amount) public {
        for (uint i = 0; i < recipients.length; i++) {
            balances[recipients[i]] += amount; // Gas-intensive operation
        }
        // Issue: If recipients.length is too large, the transaction fails
        // Attackers can exploit this by submitting large recipient lists, causing DoS
    }
    
    // Vulnerable: Unbounded loop without gas checks
    function processAllUsers() public {
        for (uint i = 0; i < users.length; i++) {
            // Gas-intensive storage operations
            balances[users[i]] = balances[users[i]] * 2;
        }
        // No gas limit checking - can run out of gas
    }
    
    // Vulnerable: While loop without gas protection
    function bulkUpdate(uint startIndex) public {
        uint i = startIndex;
        while (i < users.length) {
            balances[users[i]] += 1000;
            i++;
        }
        // No gas checks - potential DoS vector
    }
    
    // Vulnerable: Mass operations without optimization
    function massTransfer(address[] calldata recipients, uint[] calldata amounts) public {
        require(recipients.length == amounts.length, "Arrays must match");
        
        for (uint i = 0; i < recipients.length; i++) {
            // Multiple storage writes per iteration
            balances[msg.sender] -= amounts[i];
            balances[recipients[i]] += amounts[i];
            users.push(recipients[i]); // Additional gas cost
        }
        // No gas limit consideration
    }
    
    // Vulnerable: Nested loops without gas management
    function multiLevelProcess(address[][] memory userGroups) public {
        for (uint i = 0; i < userGroups.length; i++) {
            for (uint j = 0; j < userGroups[i].length; j++) {
                balances[userGroups[i][j]] += 100;
            }
        }
        // Nested loops can consume enormous amounts of gas
    }
}

contract GasOptimizedProcessing {
    mapping(address => uint) public balances;
    address[] public users;
    
    // Optimized: Uses gasleft() to gracefully exit before out of gas
    function batchTransferOptimized(address[] memory recipients, uint amount) public {
        uint i = 0;
        while (i < recipients.length && gasleft() > 50000) { // Stop before out of gas
            balances[recipients[i]] += amount;
            i++;
        }
        // Fix: Prevents complete transaction failure by handling only as many iterations as gas allows
        // Reduces DoS risk by allowing partial execution instead of reverting everything
    }
    
    // Optimized: Chunked processing with gas checks
    function processUsersChunk(uint startIndex, uint chunkSize) public {
        uint endIndex = startIndex + chunkSize;
        if (endIndex > users.length) {
            endIndex = users.length;
        }
        
        for (uint i = startIndex; i < endIndex && gasleft() > 30000; i++) {
            balances[users[i]] = balances[users[i]] * 2;
        }
    }
    
    // Optimized: Gas-aware bulk operations
    function bulkUpdateSecure(uint startIndex, uint maxOperations) public {
        uint i = startIndex;
        uint operations = 0;
        
        while (i < users.length && operations < maxOperations && gasleft() > 40000) {
            balances[users[i]] += 1000;
            i++;
            operations++;
        }
    }
    
    // Optimized: Efficient batch transfer with limits
    function massTransferSecure(
        address[] calldata recipients, 
        uint[] calldata amounts,
        uint maxTransfers
    ) public {
        require(recipients.length == amounts.length, "Arrays must match");
        
        uint transfers = 0;
        uint i = 0;
        
        while (i < recipients.length && transfers < maxTransfers && gasleft() > 60000) {
            balances[msg.sender] -= amounts[i];
            balances[recipients[i]] += amounts[i];
            
            transfers++;
            i++;
        }
    }
    
    // Optimized: Controlled nested processing
    function multiLevelProcessSecure(
        address[][] memory userGroups,
        uint maxGroups,
        uint maxUsersPerGroup
    ) public {
        uint groupsProcessed = 0;
        
        for (uint i = 0; i < userGroups.length && groupsProcessed < maxGroups && gasleft() > 100000; i++) {
            uint usersProcessed = 0;
            
            for (uint j = 0; j < userGroups[i].length && usersProcessed < maxUsersPerGroup && gasleft() > 50000; j++) {
                balances[userGroups[i][j]] += 100;
                usersProcessed++;
            }
            
            groupsProcessed++;
        }
    }
    
    // Helper function to estimate gas cost per operation
    function estimateGasCost(uint operations) public pure returns (uint) {
        return operations * 25000; // Rough estimate per operation
    }
}
