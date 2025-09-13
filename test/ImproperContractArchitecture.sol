pragma solidity ^0.8.0;

// This contract demonstrates SCWE-001: Improper Contract Architecture
// It has a monolithic design with mixed concerns and no modular patterns

contract MonolithicContract {
    // State variables for different concerns mixed together
    uint public balance;
    address public owner;
    mapping(address => uint) public allowances;
    mapping(address => bool) public authorizedUsers;
    mapping(address => uint) public userBalances;
    mapping(address => mapping(address => uint)) public userAllowances;
    
    // Events for different functionalities
    event Deposit(address indexed user, uint amount);
    event Withdrawal(address indexed user, uint amount);
    event Transfer(address indexed from, address indexed to, uint amount);
    event Authorization(address indexed user, bool status);
    event Upgrade(address indexed newImplementation);
    
    // Structs for different data types
    struct UserData {
        uint balance;
        bool isAuthorized;
        uint lastActivity;
    }
    
    struct Transaction {
        address from;
        address to;
        uint amount;
        uint timestamp;
    }
    
    // Enums for different states
    enum ContractState { Active, Paused, Upgrading }
    enum UserRole { None, User, Admin, SuperAdmin }
    
    ContractState public currentState;
    mapping(address => UserRole) public userRoles;
    
    constructor() {
        owner = msg.sender;
        currentState = ContractState.Active;
    }
    
    // Financial operations
    function deposit() public payable {
        require(currentState == ContractState.Active, "Contract is not active");
        balance += msg.value;
        userBalances[msg.sender] += msg.value;
        emit Deposit(msg.sender, msg.value);
    }
    
    function withdraw(uint amount) public {
        require(currentState == ContractState.Active, "Contract is not active");
        require(userBalances[msg.sender] >= amount, "Insufficient funds");
        require(balance >= amount, "Contract insufficient funds");
        
        balance -= amount;
        userBalances[msg.sender] -= amount;
        payable(msg.sender).transfer(amount);
        emit Withdrawal(msg.sender, amount);
    }
    
    function transfer(address to, uint amount) public {
        require(currentState == ContractState.Active, "Contract is not active");
        require(userBalances[msg.sender] >= amount, "Insufficient funds");
        
        userBalances[msg.sender] -= amount;
        userBalances[to] += amount;
        emit Transfer(msg.sender, to, amount);
    }
    
    function approve(address spender, uint amount) public {
        require(currentState == ContractState.Active, "Contract is not active");
        allowances[spender] = amount;
        userAllowances[msg.sender][spender] = amount;
    }
    
    function transferFrom(address from, address to, uint amount) public {
        require(currentState == ContractState.Active, "Contract is not active");
        require(allowances[from] >= amount, "Allowance exceeded");
        require(userBalances[from] >= amount, "Insufficient funds");
        
        allowances[from] -= amount;
        userAllowances[from][msg.sender] -= amount;
        userBalances[from] -= amount;
        userBalances[to] += amount;
        emit Transfer(from, to, amount);
    }
    
    // Access control operations
    function authorizeUser(address user) public {
        require(msg.sender == owner, "Only owner can authorize");
        require(currentState == ContractState.Active, "Contract is not active");
        
        authorizedUsers[user] = true;
        userRoles[user] = UserRole.User;
        emit Authorization(user, true);
    }
    
    function revokeAuthorization(address user) public {
        require(msg.sender == owner, "Only owner can revoke");
        require(currentState == ContractState.Active, "Contract is not active");
        
        authorizedUsers[user] = false;
        userRoles[user] = UserRole.None;
        emit Authorization(user, false);
    }
    
    function setUserRole(address user, UserRole role) public {
        require(msg.sender == owner, "Only owner can set roles");
        require(currentState == ContractState.Active, "Contract is not active");
        
        userRoles[user] = role;
    }
    
    // Business logic operations
    function calculateInterest(address user) public view returns (uint) {
        require(currentState == ContractState.Active, "Contract is not active");
        require(authorizedUsers[user], "User not authorized");
        
        uint userBalance = userBalances[user];
        uint timeSinceLastActivity = block.timestamp - userData[user].lastActivity;
        return (userBalance * timeSinceLastActivity) / 1000; // Simple interest calculation
    }
    
    function processTransaction(address from, address to, uint amount) public {
        require(currentState == ContractState.Active, "Contract is not active");
        require(authorizedUsers[msg.sender], "Not authorized to process transactions");
        require(userBalances[from] >= amount, "Insufficient funds");
        
        userBalances[from] -= amount;
        userBalances[to] += amount;
        
        // Update user data
        userData[from].lastActivity = block.timestamp;
        userData[to].lastActivity = block.timestamp;
        
        emit Transfer(from, to, amount);
    }
    
    // Admin operations
    function pauseContract() public {
        require(msg.sender == owner, "Only owner can pause");
        currentState = ContractState.Paused;
    }
    
    function resumeContract() public {
        require(msg.sender == owner, "Only owner can resume");
        currentState = ContractState.Active;
    }
    
    function upgradeContract(address newImplementation) public {
        require(msg.sender == owner, "Only owner can upgrade");
        require(currentState == ContractState.Active, "Contract must be active");
        
        currentState = ContractState.Upgrading;
        // Upgrade logic would go here - but this is impossible without proxy pattern
        emit Upgrade(newImplementation);
    }
    
    // Data management
    mapping(address => UserData) public userData;
    
    function updateUserData(address user, uint newBalance, bool isAuth) public {
        require(msg.sender == owner, "Only owner can update user data");
        require(currentState == ContractState.Active, "Contract is not active");
        
        userData[user] = UserData(newBalance, isAuth, block.timestamp);
    }
    
    function getUserData(address user) public view returns (UserData memory) {
        require(currentState == ContractState.Active, "Contract is not active");
        return userData[user];
    }
    
    // Emergency functions
    function emergencyWithdraw() public {
        require(msg.sender == owner, "Only owner can emergency withdraw");
        require(currentState == ContractState.Paused, "Contract must be paused");
        
        uint contractBalance = address(this).balance;
        payable(owner).transfer(contractBalance);
        balance = 0;
    }
    
    function destroyContract() public {
        require(msg.sender == owner, "Only owner can destroy");
        require(currentState == ContractState.Paused, "Contract must be paused");
        
        selfdestruct(payable(owner));
    }
    
    // Fallback and receive functions
    receive() external payable {
        deposit();
    }
    
    fallback() external payable {
        deposit();
    }
}
