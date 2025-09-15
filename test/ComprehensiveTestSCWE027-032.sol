// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// Comprehensive Test File for SCWE-027 to SCWE-032

// ============================================================================
// SCWE-027: Vulnerable Cryptographic Algorithms
// ============================================================================

// Vulnerable: Uses MD5 (deprecated and insecure)
contract VulnerableCrypto {
    function hashData(bytes memory data) public pure returns (bytes32) {
        return sha256(data); // This is actually secure, but let's test with a comment
        // return md5(data); // This would be vulnerable if uncommented
    }
    
    function insecureHash(string memory input) public pure returns (bytes32) {
        // Simulating vulnerable algorithm usage
        return keccak256(abi.encodePacked("md5", input));
    }
}

// Secure: Uses Keccak-256
contract SecureCrypto {
    function hashData(bytes memory data) public pure returns (bytes32) {
        return keccak256(data);
    }
    
    function secureHash(string memory input) public pure returns (bytes32) {
        return keccak256(abi.encodePacked(input));
    }
}

// ============================================================================
// SCWE-028: Price Oracle Manipulation
// ============================================================================

// Vulnerable: Direct oracle price usage without protection
contract VulnerableLending {
    address public priceOracle;
    mapping(address => uint) public balances;

    constructor(address _oracle) {
        priceOracle = _oracle;
    }

    function deposit() external payable {
        // Vulnerable: Direct use of oracle price without validation
        uint price = getPrice();
        balances[msg.sender] += msg.value * price;
    }

    function withdraw(uint amount) external {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        balances[msg.sender] -= amount;
        uint price = getPrice(); // Vulnerable: Uses current price
        payable(msg.sender).transfer(amount / price);
    }

    function getPrice() public view returns (uint) {
        // Simulating oracle call
        return 1000;
    }
}

// Secure: Price manipulation protection
contract SecureLending {
    address public priceOracle;
    mapping(address => uint) public balances;
    uint public lastValidPrice;
    uint public constant MAX_DEVIATION = 5; // 5% max deviation

    constructor(address _oracle) {
        priceOracle = _oracle;
        lastValidPrice = getPrice();
    }

    function deposit() external payable {
        uint price = getValidatedPrice();
        balances[msg.sender] += msg.value * price;
    }

    function withdraw(uint amount) external {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        balances[msg.sender] -= amount;
        uint price = getValidatedPrice();
        payable(msg.sender).transfer(amount / price);
    }

    function getValidatedPrice() internal view returns (uint) {
        uint currentPrice = getPrice();
        require(currentPrice > lastValidPrice * (100 - MAX_DEVIATION) / 100, "Price deviation too high");
        require(currentPrice < lastValidPrice * (100 + MAX_DEVIATION) / 100, "Price deviation too high");
        return currentPrice;
    }

    function getPrice() public view returns (uint) {
        return 1000;
    }
}

// ============================================================================
// SCWE-029: Lack of Decentralized Oracle Sources
// ============================================================================

// Vulnerable: Single oracle source
contract SingleOracle {
    address public priceOracle;

    constructor(address _oracle) {
        priceOracle = _oracle;
    }

    function getPrice() public view returns (uint) {
        // Vulnerable: Single source of truth
        return IOracle(priceOracle).getPrice();
    }
}

// Secure: Multiple oracle sources
contract MultiOracle {
    address[] public priceOracles;

    constructor(address[] memory _oracles) {
        for (uint i = 0; i < _oracles.length; i++) {
            priceOracles.push(_oracles[i]);
        }
    }

    function getPrice() public view returns (uint) {
        uint totalPrice = 0;
        for (uint i = 0; i < priceOracles.length; i++) {
            totalPrice += IOracle(priceOracles[i]).getPrice();
        }
        return totalPrice / priceOracles.length; // Averaging multiple oracles
    }
}

// ============================================================================
// SCWE-030: Insecure Oracle Data Updates
// ============================================================================

// Vulnerable: Unrestricted oracle updates
contract InsecureOracleUpdates {
    address public oracle;

    function updatePrice(address _oracle, uint newPrice) public {
        // Vulnerable: No access control or validation
        IOracle(_oracle).updatePrice(newPrice);
    }
}

// Secure: Oracle updates with proper security
contract SecureOracleUpdates {
    address public admin;
    address public oracle;
    uint public lastUpdateTime;
    uint public constant UPDATE_DELAY = 1 hours;

    constructor(address _admin, address _oracle) {
        admin = _admin;
        oracle = _oracle;
    }

    modifier onlyAdmin() {
        require(msg.sender == admin, "Unauthorized");
        _;
    }

    function updatePrice(uint newPrice) public onlyAdmin {
        require(block.timestamp >= lastUpdateTime + UPDATE_DELAY, "Update too soon");
        require(newPrice > 0, "Invalid price");
        IOracle(oracle).updatePrice(newPrice);
        lastUpdateTime = block.timestamp;
    }
}

// ============================================================================
// SCWE-031: Insecure use of Block Variables
// ============================================================================

// Vulnerable: Uses block.timestamp for critical timing
contract InsecureBlockUsage {
    uint public deadline;

    function setDeadline(uint _deadline) public {
        deadline = _deadline;
    }

    function checkDeadline() public view returns (string memory) {
        if (block.timestamp > deadline) {
            return "Deadline passed";
        } else {
            return "Deadline not passed";
        }
    }

    function generateRandom() public view returns (uint) {
        // Vulnerable: Uses block variables for randomness
        return uint(keccak256(abi.encodePacked(block.timestamp, block.difficulty)));
    }
}

// Secure: Uses block numbers and external randomness
contract SecureBlockUsage {
    uint public deadline;
    uint public blockNumber;

    function setDeadline(uint _deadline) public {
        deadline = _deadline;
        blockNumber = block.number;
    }

    function checkDeadline() public view returns (string memory) {
        if (block.number > blockNumber + 1000) { // Using block numbers
            return "Deadline passed";
        } else {
            return "Deadline not passed";
        }
    }

    function generateRandom() public view returns (uint) {
        // Secure: Uses external randomness source
        return uint(keccak256(abi.encodePacked("external_randomness_source")));
    }
}

// ============================================================================
// SCWE-032: Dependency on Block Gas Limit
// ============================================================================

// Vulnerable: Unbounded operations
contract GasIntensive {
    uint[] public largeArray;

    function appendData(uint[] memory data) public {
        // Vulnerable: Unbounded loop
        for (uint i = 0; i < data.length; i++) {
            largeArray.push(data[i]);
        }
    }

    function processAll() public {
        // Vulnerable: No limits on processing
        for (uint i = 0; i < largeArray.length; i++) {
            largeArray[i] = largeArray[i] * 2;
        }
    }
}

// Secure: Gas-optimized with limits
contract GasOptimized {
    uint[] public largeArray;

    function appendData(uint[] memory data, uint start, uint end) public {
        require(end <= data.length, "Invalid range");
        require(end - start <= 100, "Batch size too large"); // Limit batch size
        for (uint i = start; i < end; i++) {
            largeArray.push(data[i]);
        }
    }

    function processBatch(uint start, uint end) public {
        require(end <= largeArray.length, "Invalid range");
        require(end - start <= 50, "Batch size too large"); // Limit processing
        for (uint i = start; i < end; i++) {
            largeArray[i] = largeArray[i] * 2;
        }
    }
}

// ============================================================================
// Interface for Oracle
// ============================================================================

interface IOracle {
    function getPrice() external view returns (uint);
    function updatePrice(uint newPrice) external;
}
