// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// Test contract for assembly-related detectors

contract AssemblyTest {
    
    // S-ASM-001: Incorrect return in assembly (internal function)
    function incorrectReturn() internal returns (uint a, uint b) {
        assembly {
            return(5, 6)  // BAD: Should use 'leave' instead
        }
    }
    
    // S-ASM-002: Incorrect shift parameter order
    function incorrectShift(uint256 value) public pure returns (uint256) {
        assembly {
            // BAD: Shifts constant 8 by 'value' bits (likely wrong)
            value := shr(value, 8)
        }
        return value;
    }
    
    // GOOD: Correct shift parameter order
    function correctShift(uint256 value) public pure returns (uint256) {
        assembly {
            // GOOD: Shifts 'value' by 8 bits
            value := shr(8, value)
        }
        return value;
    }
    
    // GOOD: Correct use of leave in assembly
    function correctLeave() internal returns (uint a, uint b) {
        assembly {
            a := 5
            b := 6
            leave  // GOOD: Proper way to exit
        }
    }
    
    // Multiple shift operations
    function multipleShifts(uint256 x) public pure returns (uint256) {
        assembly {
            x := shl(x, 4)  // BAD: reversed
            x := shr(2, x)  // GOOD: correct order
            x := sar(x, 1)  // BAD: reversed
        }
        return x;
    }
}
