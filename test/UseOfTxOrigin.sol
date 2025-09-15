pragma solidity ^0.8.0;

// Vulnerable contract using tx.origin for authorization
contract VulnerableTxOrigin {
    address public owner;

    constructor() {
        owner = msg.sender;
    }

    // Vulnerable: Uses tx.origin for authorization
    function restrictedAction() public {
        require(tx.origin == owner, "Only the owner can perform this action");
        // Action code here
    }

    // Vulnerable: Uses tx.origin in if condition
    function checkOwner() public {
        if (tx.origin == owner) {
            // Some action
        }
    }

    // Vulnerable: Uses tx.origin in assignment
    function setOwner() public {
        owner = tx.origin;
    }

    // Vulnerable: Uses tx.origin in require statement
    function withdraw(uint amount) public {
        require(tx.origin == owner, "Only owner can withdraw");
        // Withdraw logic
    }

    // Vulnerable: Uses tx.origin in complex expression
    function complexCheck() public {
        require(tx.origin == owner && msg.value > 0, "Invalid transaction");
        // Some logic
    }
}

// Secure contract using msg.sender for authorization
contract SecureMsgSender {
    address public owner;

    constructor() {
        owner = msg.sender;
    }

    // Secure: Uses msg.sender for authorization
    function restrictedAction() public {
        require(msg.sender == owner, "Only the owner can perform this action");
        // Action code here
    }

    // Secure: Uses msg.sender in if condition
    function checkOwner() public {
        if (msg.sender == owner) {
            // Some action
        }
    }

    // Secure: Uses msg.sender in assignment
    function setOwner() public {
        require(msg.sender == owner, "Only owner can set owner");
        owner = msg.sender;
    }

    // Secure: Uses msg.sender in require statement
    function withdraw(uint amount) public {
        require(msg.sender == owner, "Only owner can withdraw");
        // Withdraw logic
    }

    // Secure: Uses msg.sender in complex expression
    function complexCheck() public {
        require(msg.sender == owner && msg.value > 0, "Invalid transaction");
        // Some logic
    }
}

// Contract with role-based access control using msg.sender
contract RoleBasedAccess {
    address public owner;
    mapping(address => bool) public admins;

    constructor() {
        owner = msg.sender;
        admins[msg.sender] = true;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    modifier onlyAdmin() {
        require(admins[msg.sender], "Not admin");
        _;
    }

    // Secure: Uses msg.sender with modifier
    function restrictedAction() public onlyOwner {
        // Action code here
    }

    // Secure: Uses msg.sender with modifier
    function adminAction() public onlyAdmin {
        // Admin action code here
    }

    // Secure: Uses msg.sender in require
    function addAdmin(address admin) public {
        require(msg.sender == owner, "Only owner can add admin");
        admins[admin] = true;
    }
}

// Contract with mixed usage (should flag tx.origin usage)
contract MixedUsage {
    address public owner;
    address public admin;

    constructor() {
        owner = msg.sender;
        admin = msg.sender;
    }

    // Vulnerable: Uses tx.origin
    function vulnerableAction() public {
        require(tx.origin == owner, "Only owner");
        // Action code
    }

    // Secure: Uses msg.sender
    function secureAction() public {
        require(msg.sender == admin, "Only admin");
        // Action code
    }

    // Vulnerable: Uses tx.origin in assignment
    function setAdmin() public {
        admin = tx.origin;
    }

    // Secure: Uses msg.sender in assignment
    function setOwner() public {
        require(msg.sender == owner, "Only owner");
        owner = msg.sender;
    }
}

// Contract with legitimate tx.origin usage (not for authorization)
contract LegitimateTxOrigin {
    address public owner;

    constructor() {
        owner = msg.sender;
    }

    // This is legitimate - tx.origin is used for logging, not authorization
    function logTransaction() public {
        // Log the original transaction sender for audit purposes
        // This is not used for authorization
        emit TransactionLogged(tx.origin, msg.sender, block.timestamp);
    }

    // Secure: Uses msg.sender for authorization
    function restrictedAction() public {
        require(msg.sender == owner, "Only owner");
        // Action code
    }

    event TransactionLogged(address indexed txOrigin, address indexed msgSender, uint256 timestamp);
}
