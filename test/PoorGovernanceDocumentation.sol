pragma solidity ^0.8.0;

// Contract with poor governance documentation
contract PoorGovernanceDocumentation {
    address public owner;
    address public admin;
    mapping(address => bool) public governors;
    uint public criticalValue;

    constructor() {
        owner = msg.sender;
    }

    // Undocumented governance function
    function upgrade(address newImplementation) public {
        require(msg.sender == owner, "Only owner");
        criticalValue = 1;
    }

    // Undocumented role management
    function addGovernor(address governor) public {
        require(msg.sender == owner, "Only owner");
        governors[governor] = true;
    }

    function removeGovernor(address governor) public {
        require(msg.sender == owner, "Only owner");
        governors[governor] = false;
    }

    // Undocumented critical function
    function setCriticalValue(uint newValue) public {
        require(governors[msg.sender], "Only governors");
        criticalValue = newValue;
    }

    // Undocumented emergency function
    function emergencyPause() public {
        require(msg.sender == owner, "Only owner");
        criticalValue = 0;
    }
}

// Contract with better governance documentation
contract WellDocumentedGovernance {
    /// @title Governance Contract
    /// @dev This contract implements a governance system with proper documentation
    /// @author Governance Team
    /// @notice This contract manages critical protocol parameters and upgrades
    
    address public owner;
    address public admin;
    mapping(address => bool) public governors;
    uint public criticalValue;

    /// @dev Emitted when a new governor is added
    event GovernorAdded(address indexed governor);
    
    /// @dev Emitted when a governor is removed
    event GovernorRemoved(address indexed governor);

    constructor() {
        owner = msg.sender;
    }

    /// @notice Upgrades the contract implementation
    /// @dev Only the owner can upgrade the contract
    /// @param newImplementation The address of the new implementation contract
    function upgrade(address newImplementation) public {
        require(msg.sender == owner, "Only owner can upgrade");
        criticalValue = 1;
    }

    /// @notice Adds a new governor to the governance system
    /// @dev Only the owner can add governors
    /// @param governor The address of the new governor
    function addGovernor(address governor) public {
        require(msg.sender == owner, "Only owner can add governors");
        governors[governor] = true;
        emit GovernorAdded(governor);
    }

    /// @notice Removes a governor from the governance system
    /// @dev Only the owner can remove governors
    /// @param governor The address of the governor to remove
    function removeGovernor(address governor) public {
        require(msg.sender == owner, "Only owner can remove governors");
        governors[governor] = false;
        emit GovernorRemoved(governor);
    }

    /// @notice Sets the critical value parameter
    /// @dev Only governors can set the critical value
    /// @param newValue The new value to set
    function setCriticalValue(uint newValue) public {
        require(governors[msg.sender], "Only governors can set critical value");
        criticalValue = newValue;
    }

    /// @notice Emergency pause function
    /// @dev Only the owner can pause the contract in case of emergency
    function emergencyPause() public {
        require(msg.sender == owner, "Only owner can pause");
        criticalValue = 0;
    }
}

// Contract with mixed documentation quality
contract MixedDocumentation {
    address public owner;
    mapping(address => bool) public admins;
    uint public feeRate;
    uint public maxSupply;

    constructor() {
        owner = msg.sender;
    }

    /// @notice Updates the fee rate
    /// @param newRate The new fee rate
    function updateFeeRate(uint newRate) public {
        require(msg.sender == owner, "Only owner");
        feeRate = newRate;
    }

    // Undocumented function
    function setMaxSupply(uint newSupply) public {
        require(admins[msg.sender], "Only admins");
        maxSupply = newSupply;
    }

    /// @dev Adds an admin to the system
    function addAdmin(address admin) public {
        require(msg.sender == owner, "Only owner");
        admins[admin] = true;
    }

    // Undocumented critical function
    function emergencyWithdraw() public {
        require(msg.sender == owner, "Only owner");
        feeRate = 0;
    }
}

// Contract with no governance functions (should not trigger violations)
contract NoGovernance {
    uint public value;
    string public name;

    constructor() {
        value = 42;
        name = "Test";
    }

    function setValue(uint newValue) public {
        value = newValue;
    }

    function getName() public view returns (string memory) {
        return name;
    }
}
