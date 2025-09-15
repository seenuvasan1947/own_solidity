pragma solidity ^0.8.0;

// Vulnerable contract with privileged role mismanagement
contract PrivilegedRoleMismanagement {
    address public admin;
    address public owner;
    uint public balance;
    mapping(address => bool) public roles;

    constructor() {
        owner = msg.sender;
    }

    // Vulnerable: No authorization check for role assignment
    function setAdmin(address _admin) public {
        admin = _admin;
    }

    // Vulnerable: No authorization check for role assignment
    function assignRole(address user, bool hasRole) public {
        roles[user] = hasRole;
    }

    // Vulnerable: No authorization check for role assignment
    function grantPermission(address user) public {
        roles[user] = true;
    }

    // Vulnerable: No authorization check for role assignment
    function addAdmin(address newAdmin) public {
        admin = newAdmin;
    }

    // Vulnerable: No authorization check for role assignment
    function removeRole(address user) public {
        roles[user] = false;
    }

    // Function that uses the role
    function withdraw(uint amount) public {
        require(msg.sender == admin, "Only admin can withdraw");
        balance -= amount;
    }
}

// Secure contract with proper role management
contract FixedRoleManagement {
    address public owner;
    address public admin;
    uint public balance;
    mapping(address => bool) public roles;

    constructor() {
        owner = msg.sender;
        admin = msg.sender;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Not authorized");
        _;
    }

    modifier onlyAdmin() {
        require(msg.sender == admin, "Not admin");
        _;
    }

    // Secure: Has proper authorization for role assignment
    function setAdmin(address _admin) public onlyOwner {
        admin = _admin;
    }

    // Secure: Has proper authorization for role assignment
    function assignRole(address user, bool hasRole) public onlyOwner {
        roles[user] = hasRole;
    }

    // Secure: Has proper authorization for role assignment
    function grantPermission(address user) public onlyAdmin {
        roles[user] = true;
    }

    // Secure: Has proper authorization for role assignment
    function addAdmin(address newAdmin) public onlyOwner {
        admin = newAdmin;
    }

    // Secure: Has proper authorization for role assignment
    function removeRole(address user) public onlyOwner {
        roles[user] = false;
    }

    // Function that uses the role
    function withdraw(uint amount) public onlyAdmin {
        balance -= amount;
    }
}

// Contract with role-based access control
contract RoleBasedAccessControl {
    address public owner;
    mapping(address => bool) public admins;
    mapping(address => bool) public minters;
    mapping(address => bool) public operators;
    uint public balance;

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

    modifier onlyMinter() {
        require(minters[msg.sender], "Not minter");
        _;
    }

    modifier onlyOperator() {
        require(operators[msg.sender], "Not operator");
        _;
    }

    // Secure: Only owner can add admins
    function addAdmin(address admin) public onlyOwner {
        admins[admin] = true;
    }

    // Secure: Only admin can add minters
    function addMinter(address minter) public onlyAdmin {
        minters[minter] = true;
    }

    // Secure: Only admin can add operators
    function addOperator(address operator) public onlyAdmin {
        operators[operator] = true;
    }

    // Secure: Only owner can remove admins
    function removeAdmin(address admin) public onlyOwner {
        admins[admin] = false;
    }

    // Secure: Only admin can remove minters
    function removeMinter(address minter) public onlyAdmin {
        minters[minter] = false;
    }

    // Secure: Only admin can remove operators
    function removeOperator(address operator) public onlyAdmin {
        operators[operator] = false;
    }

    // Function that uses the roles
    function withdraw(uint amount) public onlyAdmin {
        balance -= amount;
    }

    function mint(address to, uint amount) public onlyMinter {
        balance += amount;
    }

    function operate() public onlyOperator {
        // Some operation
    }
}

// Contract with internal role management (should not be flagged)
contract InternalRoleManagement {
    address public owner;
    address public admin;

    constructor() {
        owner = msg.sender;
        admin = msg.sender;
    }

    // Internal function - should not be flagged
    function _internalSetAdmin(address _admin) internal {
        admin = _admin;
    }

    // Private function - should not be flagged
    function _privateSetOwner(address _owner) private {
        owner = _owner;
    }

    // Public function that calls internal
    function setAdmin(address _admin) public {
        require(msg.sender == owner, "Only owner");
        _internalSetAdmin(_admin);
    }
}
