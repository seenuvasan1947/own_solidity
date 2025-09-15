pragma solidity ^0.8.0;

// Vulnerable contract with insufficient authorization
contract InsufficientAuthorization {
    uint public balance;
    address public owner;
    mapping(address => uint) public userBalances;

    constructor() {
        owner = msg.sender;
    }

    // Vulnerable: No authorization check
    function withdraw(uint amount) public {
        balance -= amount;
    }

    // Vulnerable: No authorization check
    function transfer(address to, uint amount) public {
        userBalances[msg.sender] -= amount;
        userBalances[to] += amount;
    }

    // Vulnerable: No authorization check
    function mint(address to, uint amount) public {
        userBalances[to] += amount;
    }

    // Vulnerable: No authorization check
    function setBalance(address user, uint newBalance) public {
        userBalances[user] = newBalance;
    }

    // Vulnerable: No authorization check
    function emergencyPause() public {
        balance = 0;
    }

    // Public getter - should not be flagged
    function getBalance() public view returns (uint) {
        return balance;
    }

    // Public getter - should not be flagged
    function getUserBalance(address user) public view returns (uint) {
        return userBalances[user];
    }
}

// Secure contract with proper authorization
contract FixedAuthorization {
    uint public balance;
    address public owner;
    mapping(address => uint) public userBalances;

    constructor() {
        owner = msg.sender;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Not authorized");
        _;
    }

    // Secure: Has authorization modifier
    function withdraw(uint amount) public onlyOwner {
        balance -= amount;
    }

    // Secure: Has authorization check
    function transfer(address to, uint amount) public {
        require(msg.sender == owner, "Only owner can transfer");
        userBalances[msg.sender] -= amount;
        userBalances[to] += amount;
    }

    // Secure: Has authorization modifier
    function mint(address to, uint amount) public onlyOwner {
        userBalances[to] += amount;
    }

    // Secure: Has authorization check
    function setBalance(address user, uint newBalance) public {
        require(owner == msg.sender, "Only owner can set balance");
        userBalances[user] = newBalance;
    }

    // Secure: Has authorization modifier
    function emergencyPause() public onlyOwner {
        balance = 0;
    }

    // Public getter - should not be flagged
    function getBalance() public view returns (uint) {
        return balance;
    }

    // Public getter - should not be flagged
    function getUserBalance(address user) public view returns (uint) {
        return userBalances[user];
    }
}

// Contract with role-based access control
contract RoleBasedAccess {
    address public owner;
    mapping(address => bool) public admins;
    mapping(address => bool) public minters;
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

    // Secure: Has proper role-based authorization
    function withdraw(uint amount) public onlyOwner {
        balance -= amount;
    }

    // Secure: Has proper role-based authorization
    function mint(address to, uint amount) public onlyMinter {
        balance += amount;
    }

    // Secure: Has proper role-based authorization
    function addAdmin(address admin) public onlyOwner {
        admins[admin] = true;
    }

    // Secure: Has proper role-based authorization
    function addMinter(address minter) public onlyAdmin {
        minters[minter] = true;
    }
}

// Contract with internal functions (should not be flagged)
contract InternalFunctions {
    uint public balance;
    address public owner;

    constructor() {
        owner = msg.sender;
    }

    // Internal function - should not be flagged
    function _internalTransfer(address to, uint amount) internal {
        balance -= amount;
    }

    // Private function - should not be flagged
    function _privateUpdate(uint newBalance) private {
        balance = newBalance;
    }

    // Public function that calls internal
    function transfer(address to, uint amount) public {
        require(msg.sender == owner, "Only owner");
        _internalTransfer(to, amount);
    }
}
