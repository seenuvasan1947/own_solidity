pragma solidity ^0.8.0;

// Vulnerable contract with unauthorized parameter changes
contract RiskyContract {
    address public owner;
    uint256 public feeRate;
    uint256 public maxSupply;
    uint256 public withdrawalLimit;
    uint256 public price;

    constructor() {
        owner = msg.sender;
        feeRate = 5;
        maxSupply = 1000000;
        withdrawalLimit = 1000;
        price = 100;
    }

    // Vulnerable: No access control for critical parameter changes
    function updateFeeRate(uint256 newRate) public {
        feeRate = newRate;
    }

    function setMaxSupply(uint256 newSupply) public {
        maxSupply = newSupply;
    }

    function changeWithdrawalLimit(uint256 newLimit) public {
        withdrawalLimit = newLimit;
    }

    function modifyPrice(uint256 newPrice) public {
        price = newPrice;
    }

    // Vulnerable: Only basic owner check, no governance
    function configureSettings(uint256 newFee, uint256 newLimit) public {
        require(msg.sender == owner, "Only owner");
        feeRate = newFee;
        withdrawalLimit = newLimit;
    }
}

// Secure contract with proper governance mechanisms
contract SecureGovernance {
    address public multisigWallet;
    uint256 public feeRate;
    uint256 public maxSupply;
    uint256 public withdrawalLimit;
    uint256 public price;
    
    // Timelock for parameter changes
    uint256 public constant TIMELOCK_DELAY = 2 days;
    mapping(bytes32 => uint256) public queuedTransactions;

    constructor(address _multisigWallet) {
        multisigWallet = _multisigWallet;
        feeRate = 5;
        maxSupply = 1000000;
        withdrawalLimit = 1000;
        price = 100;
    }

    modifier onlyMultisig() {
        require(msg.sender == multisigWallet, "Only multisig wallet");
        _;
    }

    // Secure: Requires multisig approval
    function updateFeeRate(uint256 newRate) public onlyMultisig {
        feeRate = newRate;
    }

    function setMaxSupply(uint256 newSupply) public onlyMultisig {
        maxSupply = newSupply;
    }

    function changeWithdrawalLimit(uint256 newLimit) public onlyMultisig {
        withdrawalLimit = newLimit;
    }

    function modifyPrice(uint256 newPrice) public onlyMultisig {
        price = newPrice;
    }

    // Secure: Uses timelock mechanism
    function queueParameterChange(
        uint256 newFee,
        uint256 newLimit,
        uint256 newPrice
    ) public onlyMultisig {
        bytes32 txHash = keccak256(abi.encodePacked(newFee, newLimit, newPrice, block.timestamp));
        queuedTransactions[txHash] = block.timestamp + TIMELOCK_DELAY;
    }

    function executeParameterChange(
        uint256 newFee,
        uint256 newLimit,
        uint256 newPrice
    ) public onlyMultisig {
        bytes32 txHash = keccak256(abi.encodePacked(newFee, newLimit, newPrice, block.timestamp - TIMELOCK_DELAY));
        require(queuedTransactions[txHash] > 0, "Transaction not queued");
        require(block.timestamp >= queuedTransactions[txHash], "Timelock not expired");
        
        feeRate = newFee;
        withdrawalLimit = newLimit;
        price = newPrice;
        
        delete queuedTransactions[txHash];
    }
}

// Contract with DAO governance
contract DAOGovernance {
    address public governance;
    uint256 public feeRate;
    uint256 public maxSupply;

    constructor(address _governance) {
        governance = _governance;
        feeRate = 5;
        maxSupply = 1000000;
    }

    modifier onlyGovernance() {
        require(msg.sender == governance, "Only governance");
        _;
    }

    // Secure: Requires DAO governance approval
    function updateFeeRate(uint256 newRate) public onlyGovernance {
        feeRate = newRate;
    }

    function setMaxSupply(uint256 newSupply) public onlyGovernance {
        maxSupply = newSupply;
    }
}

// Contract with role-based access control
contract RoleBasedAccess {
    mapping(address => bool) public admins;
    uint256 public feeRate;
    uint256 public maxSupply;

    constructor() {
        admins[msg.sender] = true;
        feeRate = 5;
        maxSupply = 1000000;
    }

    modifier onlyAdmin() {
        require(admins[msg.sender], "Only admin");
        _;
    }

    function addAdmin(address admin) public onlyAdmin {
        admins[admin] = true;
    }

    // Secure: Uses role-based access control
    function updateFeeRate(uint256 newRate) public onlyAdmin {
        feeRate = newRate;
    }

    function setMaxSupply(uint256 newSupply) public onlyAdmin {
        maxSupply = newSupply;
    }
}
