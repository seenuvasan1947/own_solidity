// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// Test contract for SCWE-039: Insecure Use of Inline Assembly
// This contract demonstrates vulnerable patterns in inline assembly usage

contract InsecureAssembly {
    uint256 public balance;
    
    // Vulnerable: Unsafe type casting without bounds checking
    function unsafeCast(uint256 value) public pure returns (uint8) {
        uint8 result;
        assembly {
            result := value // Unsafe cast, truncating high bits
        }
        return result;
        // Why is this vulnerable?
        // - Casting a large uint256 into uint8 without bounds checking causes integer truncation
        // - If value = 257, it becomes 1 (256 is lost)
        // - Attackers can bypass security checks if truncation affects authentication or balance checks
    }
    
    // Vulnerable: Direct memory manipulation without validation
    function unsafeMemoryWrite(uint256 offset, uint256 value) public {
        assembly {
            mstore(offset, value) // Direct memory write without validation
        }
        // No input validation - attacker can write to arbitrary memory locations
        // Could overwrite critical contract data or cause undefined behavior
    }
    
    // Vulnerable: Storage manipulation without checks
    function unsafeStorageWrite(uint256 slot, uint256 value) public {
        assembly {
            sstore(slot, value) // Direct storage write without access control
        }
        // Anyone can modify any storage slot
        // Could overwrite owner, balances, or other critical state
    }
    
    // Vulnerable: Unsafe external call via assembly
    function unsafeCall(address target, bytes memory data) public returns (bool success) {
        assembly {
            success := call(gas(), target, 0, add(data, 0x20), mload(data), 0, 0)
        }
        // No validation of target address or call data
        // Could be used for reentrancy attacks or malicious calls
    }
    
    // Vulnerable: Contract creation without validation
    function unsafeCreate(bytes memory bytecode) public returns (address addr) {
        assembly {
            addr := create(0, add(bytecode, 0x20), mload(bytecode))
        }
        // No validation of bytecode
        // Attacker could deploy malicious contracts
    }
    
    // Vulnerable: Complex assembly operation without input validation
    function complexUnsafeOperation(uint256 a, uint256 b, uint8 c) public pure returns (uint256 result) {
        assembly {
            // Multiple operations without validation
            let temp := add(a, b)
            let shifted := shl(c, temp)  // Shift by c bits
            result := and(shifted, 0xFF) // Mask to 8 bits - potential truncation
        }
        // No bounds checking on inputs
        // c could be > 255, causing unexpected behavior
        // Result truncation without validation
    }
}

contract SecureAssembly {
    uint256 public balance;
    address public owner;
    
    constructor() {
        owner = msg.sender;
    }
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Not authorized");
        _;
    }
    
    // Secure: Proper bounds checking before type conversion
    function safeCast(uint256 value) public pure returns (uint8) {
        require(value <= type(uint8).max, "Value too large"); // Prevent truncation
        return uint8(value);
        // Fixes:
        // - Bounds checking (require) prevents unintended truncation
        // - Uses high-level Solidity instead of assembly when possible
    }
    
    // Secure: Assembly with input validation
    function safeMemoryOperation(uint256 offset, uint256 value) public pure returns (uint256 result) {
        require(offset < 0x1000, "Offset too large"); // Validate offset
        require(value != 0, "Value cannot be zero"); // Validate value
        
        assembly {
            mstore(offset, value)
            result := mload(offset)
        }
        // Input validation prevents dangerous memory operations
    }
    
    // Secure: Storage access with proper authorization
    function safeStorageWrite(uint256 value) public onlyOwner {
        require(value > 0, "Value must be positive");
        
        assembly {
            sstore(0, value) // Only write to specific, controlled slot
        }
        // Access control and input validation
        // Limited to specific storage slot
    }
    
    // Secure: External call with validation
    function safeCall(address target, bytes memory data) public onlyOwner returns (bool success) {
        require(target != address(0), "Invalid target");
        require(data.length > 0, "Empty data");
        require(target.code.length > 0, "Target is not a contract");
        
        assembly {
            success := call(gas(), target, 0, add(data, 0x20), mload(data), 0, 0)
        }
        // Multiple validation checks before assembly call
        // Access control to prevent unauthorized calls
    }
    
    // Secure: Assembly with comprehensive bounds checking
    function safeComplexOperation(uint256 a, uint256 b, uint8 c) public pure returns (uint256 result) {
        require(a <= type(uint128).max, "a too large");
        require(b <= type(uint128).max, "b too large");
        require(c <= 8, "Shift amount too large"); // Prevent excessive shifting
        
        assembly {
            let temp := add(a, b)
            // Check for overflow in assembly
            if lt(temp, a) { revert(0, 0) }
            
            let shifted := shl(c, temp)
            result := and(shifted, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF) // Proper mask
        }
        // Comprehensive input validation
        // Overflow checking within assembly
        // Controlled bit operations
    }
    
    // Best practice: Avoid assembly when high-level Solidity suffices
    function preferHighLevel(uint256 value) public pure returns (uint256) {
        // Instead of assembly, use built-in operations
        return value * 2; // Simple, safe, readable
        // No assembly needed for basic operations
    }
}

contract MinimalAssemblyUsage {
    // Example of justified assembly usage with proper safeguards
    function efficientHash(bytes32 a, bytes32 b) public pure returns (bytes32 result) {
        // Input validation
        require(a != bytes32(0), "First input cannot be zero");
        require(b != bytes32(0), "Second input cannot be zero");
        
        // Assembly justified for gas optimization in hash computation
        assembly {
            mstore(0x00, a)
            mstore(0x20, b)
            result := keccak256(0x00, 0x40)
        }
        // Assembly usage is:
        // 1. Justified (gas optimization)
        // 2. Validated (input checks)
        // 3. Limited in scope
        // 4. Well-documented
    }
}
