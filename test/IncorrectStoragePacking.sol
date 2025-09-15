// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// Test contract for SCWE-040: Incorrect Storage Packing
// This contract demonstrates inefficient storage packing patterns

contract InefficientStorage {
    // Inefficient packing - each variable unnecessarily occupies separate slots
    uint256 a;  // Slot 0: Occupies full 32-byte slot
    bool b;     // Slot 1: Occupies another 32-byte slot (wasteful) - only needs 1 byte
    uint8 c;    // Slot 2: Uses a new 32-byte slot instead of sharing - only needs 1 byte
    uint256 d;  // Slot 3: Uses its own slot, leading to extra gas costs
    
    // More inefficient patterns
    uint128 e;  // Slot 4: Uses 16 bytes, wastes 16 bytes
    bool f;     // Slot 5: Could have been packed with 'e'
    uint64 g;   // Slot 6: Uses 8 bytes, wastes 24 bytes
    uint32 h;   // Slot 7: Could have been packed with 'g'
    uint16 i;   // Slot 8: Could have been packed with 'g' and 'h'
    
    // Scattered small variables
    uint256 large1;  // Slot 9
    uint8 small1;    // Slot 10
    uint256 large2;  // Slot 11
    uint8 small2;    // Slot 12 - could be packed with small1
    uint256 large3;  // Slot 13
    uint8 small3;    // Slot 14 - could be packed with small1 and small2
    
    // Scattered booleans
    uint256 data1;   // Slot 15
    bool flag1;      // Slot 16
    uint256 data2;   // Slot 17
    bool flag2;      // Slot 18 - could be packed with flag1
    uint256 data3;   // Slot 19
    bool flag3;      // Slot 20 - could be packed with flag1 and flag2
    
    // Why is this inefficient?
    // - Each variable unnecessarily occupies a separate storage slot
    // - The bool and uint8 variables could be packed into the same 32-byte slots
    // - Results in wasted storage space and higher gas costs
    // - Reading/writing multiple small variables requires multiple SLOAD/SSTORE operations
}

contract OptimizedStorage {
    // Efficient packing - variables grouped by size and usage patterns
    
    // Group 1: Full-slot variables together
    uint256 a;   // Slot 0: Occupies one full 32-byte slot
    uint256 d;   // Slot 1: Placed next to 'a' to use another full slot
    uint256 large1; // Slot 2
    uint256 large2; // Slot 3
    uint256 large3; // Slot 4
    uint256 data1;  // Slot 5
    uint256 data2;  // Slot 6
    uint256 data3;  // Slot 7
    
    // Group 2: Pack smaller variables together
    uint128 e;   // Slot 8: Uses 16 bytes
    uint64 g;    // Slot 8: Uses 8 bytes (packed with e, total 24 bytes)
    uint32 h;    // Slot 8: Uses 4 bytes (packed with e,g, total 28 bytes)
    // 4 bytes remaining in slot 8
    
    // Group 3: Pack very small variables
    bool b;      // Slot 9: Uses 1 byte
    bool f;      // Slot 9: Uses 1 byte (packed with b)
    bool flag1;  // Slot 9: Uses 1 byte (packed with b,f)
    bool flag2;  // Slot 9: Uses 1 byte (packed with b,f,flag1)
    bool flag3;  // Slot 9: Uses 1 byte (packed with b,f,flag1,flag2)
    uint8 c;     // Slot 9: Uses 1 byte (packed with bools)
    uint8 small1; // Slot 9: Uses 1 byte (packed with others)
    uint8 small2; // Slot 9: Uses 1 byte (packed with others)
    uint8 small3; // Slot 9: Uses 1 byte (packed with others)
    uint16 i;    // Slot 9: Uses 2 bytes (packed with others, total usage: 11 bytes)
    // 21 bytes remaining in slot 9
    
    // Why is this better?
    // - bool and uint8 variables share the same storage slot
    // - uint256 variables are placed together to minimize fragmentation
    // - Optimized storage layout leads to lower gas costs for contract execution
    // - Fewer SLOAD/SSTORE operations needed for related data
}

contract MixedPatterns {
    // Some good, some bad patterns for testing detection
    
    // Good: Grouped small types
    bool active;
    bool paused;
    uint8 status;
    uint16 count;
    // These should pack into one slot (1+1+1+2 = 5 bytes)
    
    // Bad: Large type interrupting small types
    uint256 largeData; // This separates the above from below
    
    // More small types that could have been with the first group
    bool enabled;
    uint8 level;
    
    // Good: Another group of large types
    uint256 balance;
    uint256 totalSupply;
    
    // Bad: Single small type alone
    uint8 decimals; // This wastes most of a slot
}

contract WorstCaseScenario {
    // Extremely inefficient - alternating large and small types
    uint256 big1;
    bool tiny1;
    uint256 big2;
    uint8 tiny2;
    uint256 big3;
    uint16 tiny3;
    uint256 big4;
    uint32 tiny4;
    uint256 big5;
    bool tiny5;
    
    // This pattern wastes enormous amounts of storage
    // Each small variable gets its own 32-byte slot
    // Could be optimized to use much fewer slots
}

contract ReasonableUsage {
    // Acceptable patterns that shouldn't trigger warnings
    
    // Single variables of any size are fine
    uint256 singleLargeVar;
    
    // Well-packed groups
    uint128 half1;
    uint128 half2; // These two perfectly fill one slot
    
    // Small group that's well-packed
    uint64 quarter1;
    uint64 quarter2;
    uint64 quarter3;
    uint64 quarter4; // Four uint64s perfectly fill one slot
    
    // Bools grouped together
    bool flag1;
    bool flag2;
    bool flag3;
    bool flag4; // Multiple bools in one slot is good
}
