pragma solidity ^0.4.0;

// Contract with hardcoded constants - should be detected by SCWE-008 rule
contract HardcodedConstants {
    address public owner = 0x1234567890abcdef1234567890abcdef12345678; // Hardcoded address
    uint public maxSupply = 1000000; // Hardcoded large number
    string public tokenName = "MyToken"; // Hardcoded string
    uint public constant FEE_RATE = 500; // Hardcoded constant
    address public constant TREASURY = 0xabcdef1234567890abcdef1234567890abcdef12; // Hardcoded constant address

    function setOwner(address newOwner) public {
        owner = newOwner;
    }

    function setMaxSupply(uint newMaxSupply) public {
        maxSupply = newMaxSupply;
    }
    
    function processPayment() public {
        uint hardcodedAmount = 1000000000000000000; // 1 ETH in wei - hardcoded
        string memory hardcodedMessage = "Payment processed"; // Hardcoded string
        address hardcodedRecipient = 0x9876543210fedcba9876543210fedcba98765432; // Hardcoded address
        
        // These should be detected as hardcoded constants
    }
    
    function calculateFee(uint amount) public pure returns (uint) {
        uint fee = amount * 25 / 1000; // 2.5% fee - hardcoded percentage
        return fee;
    }
}

// Contract without hardcoded constants - should NOT be detected
contract ConfigurableContract {
    address public owner;
    uint public maxSupply;
    string public tokenName;
    uint public feeRate;

    constructor(address initialOwner, uint initialMaxSupply, string initialTokenName, uint initialFeeRate) public {
        owner = initialOwner;
        maxSupply = initialMaxSupply;
        tokenName = initialTokenName;
        feeRate = initialFeeRate;
    }

    function setOwner(address newOwner) public {
        owner = newOwner;
    }

    function setMaxSupply(uint newMaxSupply) public {
        maxSupply = newMaxSupply;
    }
    
    function setTokenName(string newTokenName) public {
        tokenName = newTokenName;
    }
    
    function setFeeRate(uint newFeeRate) public {
        feeRate = newFeeRate;
    }
    
    function processPayment(uint amount, address recipient) public {
        uint fee = amount * feeRate / 1000; // Using configurable fee rate
        // No hardcoded values
    }
}
