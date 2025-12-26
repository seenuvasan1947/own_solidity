// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * Test contract for Operations Rules
 * Tests: S-SEC-009, S-SEC-015, S-SEC-016, S-OPT-002, S-CODE-011
 */

contract OperationsRulesTest {
    
    // ============================================
    // S-SEC-009: Weak PRNG Detection Tests
    // ============================================
    
    uint256 public randomNumber;
    uint256[] public storageArray;
    
    // SHOULD FLAG: Using block.timestamp with modulo for randomness
    function weakPRNG_timestamp() public {
        randomNumber = block.timestamp % 100;  // ❌ S-SEC-009
    }
    
    // SHOULD FLAG: Using blockhash with modulo
    function weakPRNG_blockhash() public {
        randomNumber = uint256(blockhash(block.number - 1)) % 100;  // ❌ S-SEC-009
    }
    
    // SHOULD NOT FLAG: Simple time check (not randomness)
    function safeTimeCheck() public view {
        require(block.timestamp > 1000000, "Too early");
    }
    
    // ============================================
    // S-SEC-015: Block Timestamp Manipulation Tests
    // ============================================
    
    // SHOULD FLAG: Timestamp in require with short interval
    function dangerousTimestampCheck(uint256 deadline) public {
        require(block.timestamp < deadline, "Expired");  // ⚠️  S-SEC-015
    }
    
    // SHOULD NOT FLAG: Long time lock (days)
    function safeTimeLock() public view {
        require(block.timestamp > block.timestamp + 7 days, "Locked");
    }
    
    // SHOULD FLAG: Timestamp-dependent state change
    function timestampDependentTransfer(address to) public {
        if (block.timestamp % 2 == 0) {  // ⚠️  S-SEC-015
            payable(to).transfer(1 ether);
        }
    }
    
    // SHOULD NOT FLAG: View function
    function viewTimestamp() public view returns (uint256) {
        return block.timestamp;
    }
    
    // ============================================
    // S-OPT-002: Cache Array Length Tests
    // ============================================
    
    // SHOULD FLAG: Storage array length not cached
    function uncachedArrayLength() public {
        for (uint256 i = 0; i < storageArray.length; i++) {  // 💡 S-OPT-002
            // Do something
            storageArray[i] = i;
        }
    }
    
    // SHOULD NOT FLAG: Array length is cached
    function cachedArrayLength() public {
        uint256 length = storageArray.length;
        for (uint256 i = 0; i < length; i++) {
            storageArray[i] = i;
        }
    }
    
    // SHOULD NOT FLAG: Memory array
    function memoryArrayLoop() public pure {
        uint256[] memory tempArray = new uint256[](10);
        for (uint256 i = 0; i < tempArray.length; i++) {
            tempArray[i] = i;
        }
    }
    
    // SHOULD NOT FLAG: Loop modifies array
    function arrayModifyingLoop() public {
        for (uint256 i = 0; i < storageArray.length; i++) {
            if (i % 2 == 0) {
                storageArray.push(i);  // Modifies array
            }
        }
    }
    
    // ============================================
    // S-SEC-016: ABI EncodePacked Collision Tests
    // ============================================
    
    // SHOULD FLAG: Multiple dynamic types in encodePacked with keccak256
    function dangerousEncodePacked(string memory name, string memory data) public pure returns (bytes32) {
        return keccak256(abi.encodePacked(name, data));  // ❌ S-SEC-016 CRITICAL
    }
    
    // SHOULD FLAG: Multiple bytes in encodePacked
    function multipleBytes(bytes memory a, bytes memory b) public pure returns (bytes32) {
        return keccak256(abi.encodePacked(a, b));  // ❌ S-SEC-016 CRITICAL
    }
    
    // SHOULD NOT FLAG: Single dynamic type
    function singleDynamicType(string memory name) public pure returns (bytes32) {
        return keccak256(abi.encodePacked(name));
    }
    
    // SHOULD NOT FLAG: Using abi.encode instead
    function safeEncode(string memory name, string memory data) public pure returns (bytes32) {
        return keccak256(abi.encode(name, data));
    }
    
    // SHOULD NOT FLAG: Fixed-size types only
    function fixedSizeTypes(uint256 a, address b) public pure returns (bytes32) {
        return keccak256(abi.encodePacked(a, b));
    }
    
    // ============================================
    // S-CODE-011: Incorrect Exponentiation Tests
    // ============================================
    
    // SHOULD FLAG: Using ^ instead of ** for exponentiation
    uint256 public constant MAX_UINT = 2^256 - 1;  // ❌ S-CODE-011 CRITICAL
    
    // SHOULD FLAG: Token decimals with wrong operator
    uint256 public constant DECIMALS = 10^18;  // ❌ S-CODE-011 CRITICAL
    
    // SHOULD NOT FLAG: Correct exponentiation
    uint256 public constant CORRECT_MAX = 2**256 - 1;
    uint256 public constant CORRECT_DECIMALS = 10**18;
    
    // SHOULD NOT FLAG: Intentional XOR with hex
    function intentionalXOR() public pure returns (uint256) {
        return 0xFF ^ 0x0F;  // Intentional bitwise XOR
    }
    
    // SHOULD FLAG: Power of 2 with ^
    function incorrectPowerOf2() public pure returns (uint256) {
        return 2^8;  // ❌ S-CODE-011 CRITICAL (should be 2**8 = 256, not 2^8 = 10)
    }
    
    // SHOULD NOT FLAG: Correct power of 2
    function correctPowerOf2() public pure returns (uint256) {
        return 2**8;  // 256
    }
    
    // ============================================
    // Combined Test Cases
    // ============================================
    
    // Multiple violations in one function
    function multipleViolations(string memory name, string memory data) public {
        // S-SEC-009: Weak PRNG
        uint256 random = block.timestamp % 100;
        
        // S-SEC-015: Timestamp manipulation
        require(block.timestamp > 1000, "Too early");
        
        // S-OPT-002: Uncached array length
        for (uint256 i = 0; i < storageArray.length; i++) {
            storageArray[i] = random;
        }
        
        // S-SEC-016: EncodePacked collision
        bytes32 hash = keccak256(abi.encodePacked(name, data));
        
        // S-CODE-011: Incorrect exponentiation
        uint256 value = 10^6;  // Should be 10**6
    }
    
    // Safe implementation
    function safeImplementation() public {
        // Use Chainlink VRF for randomness (not block.timestamp)
        // Use block.number for short intervals
        // Cache array length
        uint256 length = storageArray.length;
        for (uint256 i = 0; i < length; i++) {
            storageArray[i] = i;
        }
        // Use abi.encode for hashing
        // Use ** for exponentiation
        uint256 value = 10**6;
    }
}

/**
 * Expected Violations Summary:
 * 
 * S-SEC-009 (Weak PRNG):
 * - Line ~23: weakPRNG_timestamp() - block.timestamp % 100
 * - Line ~28: weakPRNG_blockhash() - blockhash with modulo
 * - Line ~113: multipleViolations() - block.timestamp % 100
 * 
 * S-SEC-015 (Block Timestamp):
 * - Line ~41: dangerousTimestampCheck() - timestamp in require
 * - Line ~51: timestampDependentTransfer() - timestamp-dependent state change
 * - Line ~115: multipleViolations() - timestamp in require
 * 
 * S-OPT-002 (Cache Array Length):
 * - Line ~67: uncachedArrayLength() - storage array length not cached
 * - Line ~119: multipleViolations() - storage array length not cached
 * 
 * S-SEC-016 (EncodePacked Collision):
 * - Line ~98: dangerousEncodePacked() - multiple strings with keccak256
 * - Line ~103: multipleBytes() - multiple bytes with keccak256
 * - Line ~123: multipleViolations() - multiple strings with keccak256
 * 
 * S-CODE-011 (Incorrect Exponentiation):
 * - Line ~126: MAX_UINT - 2^256 instead of 2**256
 * - Line ~129: DECIMALS - 10^18 instead of 10**18
 * - Line ~140: incorrectPowerOf2() - 2^8 instead of 2**8
 * - Line ~126: multipleViolations() - 10^6 instead of 10**6
 * 
 * Total Expected Violations: ~16
 */
