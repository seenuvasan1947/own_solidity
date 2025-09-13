pragma solidity ^0.8.0;

// Contract with insecure ABI encoding - should be detected by SCWE-011 rule
contract InsecureABI {
    // Insecure: abi.encodePacked with keccak256 (collision risk)
    function hashValues(string memory str, uint256 num) public pure returns (bytes32) {
        return keccak256(abi.encodePacked(str, num)); // Collision risk
    }
    
    // Insecure: abi.encodePacked with multiple parameters (collision risk)
    function hashMultipleValues(string memory str1, string memory str2, uint256 num) public pure returns (bytes32) {
        return keccak256(abi.encodePacked(str1, str2, num)); // High collision risk
    }
    
    // Insecure: abi.encodePacked without keccak256 (still potentially risky)
    function encodeValues(string memory str, uint256 num) public pure returns (bytes memory) {
        return abi.encodePacked(str, num); // Potentially insecure
    }
    
    // Insecure: abi.decode without proper validation
    function decodeData(bytes memory data) public pure returns (string memory, uint256) {
        return abi.decode(data, (string, uint256)); // No validation
    }
    
    // Insecure: abi.decode with external data
    function processExternalData(bytes memory externalData) public pure returns (address) {
        (address addr) = abi.decode(externalData, (address)); // External data without validation
        return addr;
    }
    
    // Insecure: Complex abi.encodePacked with mixed types
    function complexHash(address addr, string memory name, uint256[] memory numbers) public pure returns (bytes32) {
        return keccak256(abi.encodePacked(addr, name, numbers)); // Complex collision risk
    }
}

// Contract with secure ABI encoding - should NOT be detected
contract SecureABI {
    // Secure: abi.encode with keccak256 (no collision risk)
    function hashValues(string memory str, uint256 num) public pure returns (bytes32) {
        return keccak256(abi.encode(str, num)); // Secure encoding
    }
    
    // Secure: abi.encode with multiple parameters
    function hashMultipleValues(string memory str1, string memory str2, uint256 num) public pure returns (bytes32) {
        return keccak256(abi.encode(str1, str2, num)); // Secure encoding
    }
    
    // Secure: abi.encode for general encoding
    function encodeValues(string memory str, uint256 num) public pure returns (bytes memory) {
        return abi.encode(str, num); // Secure encoding
    }
    
    // Secure: abi.decode with validation
    function decodeData(bytes memory data) public pure returns (string memory, uint256) {
        require(data.length > 0, "Empty data"); // Validation
        return abi.decode(data, (string, uint256));
    }
    
    // Secure: abi.decode with proper error handling
    function processValidatedData(bytes memory validatedData) public pure returns (address) {
        require(validatedData.length >= 32, "Invalid data length"); // Validation
        (address addr) = abi.decode(validatedData, (address));
        require(addr != address(0), "Invalid address"); // Additional validation
        return addr;
    }
    
    // Secure: abi.encode for complex data
    function complexHash(address addr, string memory name, uint256[] memory numbers) public pure returns (bytes32) {
        return keccak256(abi.encode(addr, name, numbers)); // Secure encoding
    }
    
    // Secure: Using abi.encodePacked for non-hashing purposes (acceptable)
    function createSignature(string memory message, uint256 nonce) public pure returns (bytes memory) {
        // This is acceptable as it's not used for hashing
        return abi.encodePacked(message, nonce);
    }
}
