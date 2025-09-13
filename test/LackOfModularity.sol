// Test file for LackOfModularityDetector
// This file contains examples of lack of modularity as defined in SCWE-003

pragma solidity ^0.8.0;

// Example 1: Monolithic contract with too many responsibilities (violates modularity)
contract TightlyCoupledContract {
    // Too many state variables - will trigger violation
    mapping(address => uint) public balances;
    mapping(address => mapping(address => uint)) public allowances;
    mapping(address => bool) public isPaused;
    mapping(address => uint) public lastActivity;
    mapping(address => bool) public isWhitelisted;
    mapping(address => uint) public stakingAmount;
    mapping(address => uint) public rewardRate;
    mapping(address => uint) public lastClaimTime;
    mapping(address => bool) public isAdmin;
    mapping(address => bool) public isModerator;
    mapping(address => uint) public reputation;
    mapping(address => uint) public totalStaked;
    
    address public owner;
    uint public totalSupply;
    uint public maxSupply;
    bool public paused;
    uint public stakingPeriod;
    uint public rewardMultiplier;
    uint public feeRate;
    uint public minStakeAmount;
    uint public maxStakeAmount;
    
    // Too many functions with multiple responsibilities - will trigger violations
    function deposit() public payable {
        balances[msg.sender] += msg.value;
        lastActivity[msg.sender] = block.timestamp;
    }
    
    function withdraw(uint amount) public {
        require(balances[msg.sender] >= amount, "Insufficient funds");
        require(!isPaused[msg.sender], "Account paused");
        balances[msg.sender] -= amount;
        payable(msg.sender).transfer(amount);
        lastActivity[msg.sender] = block.timestamp;
    }
    
    function transfer(address to, uint amount) public {
        require(balances[msg.sender] >= amount, "Insufficient funds");
        require(!isPaused[msg.sender], "Account paused");
        balances[msg.sender] -= amount;
        balances[to] += amount;
        lastActivity[msg.sender] = block.timestamp;
        lastActivity[to] = block.timestamp;
    }
    
    function approve(address spender, uint amount) public {
        allowances[msg.sender][spender] = amount;
        lastActivity[msg.sender] = block.timestamp;
    }
    
    function transferFrom(address from, address to, uint amount) public {
        require(allowances[from][msg.sender] >= amount, "Allowance exceeded");
        require(balances[from] >= amount, "Insufficient funds");
        require(!isPaused[from], "From account paused");
        allowances[from][msg.sender] -= amount;
        balances[from] -= amount;
        balances[to] += amount;
        lastActivity[from] = block.timestamp;
        lastActivity[to] = block.timestamp;
    }
    
    function pauseAccount(address account) public {
        require(isAdmin[msg.sender] || isModerator[msg.sender], "Not authorized");
        isPaused[account] = true;
    }
    
    function unpauseAccount(address account) public {
        require(isAdmin[msg.sender] || isModerator[msg.sender], "Not authorized");
        isPaused[account] = false;
    }
    
    function addToWhitelist(address account) public {
        require(isAdmin[msg.sender], "Not admin");
        isWhitelisted[account] = true;
    }
    
    function removeFromWhitelist(address account) public {
        require(isAdmin[msg.sender], "Not admin");
        isWhitelisted[account] = false;
    }
    
    function stake(uint amount) public {
        require(balances[msg.sender] >= amount, "Insufficient funds");
        require(amount >= minStakeAmount, "Below minimum stake");
        require(amount <= maxStakeAmount, "Above maximum stake");
        balances[msg.sender] -= amount;
        stakingAmount[msg.sender] += amount;
        totalStaked[msg.sender] += amount;
        lastClaimTime[msg.sender] = block.timestamp;
    }
    
    function unstake(uint amount) public {
        require(stakingAmount[msg.sender] >= amount, "Insufficient staked amount");
        require(block.timestamp >= lastClaimTime[msg.sender] + stakingPeriod, "Staking period not over");
        stakingAmount[msg.sender] -= amount;
        totalStaked[msg.sender] -= amount;
        balances[msg.sender] += amount;
    }
    
    function claimRewards() public {
        require(stakingAmount[msg.sender] > 0, "No staked amount");
        uint timePassed = block.timestamp - lastClaimTime[msg.sender];
        uint rewards = (stakingAmount[msg.sender] * rewardRate[msg.sender] * timePassed) / 1 days;
        balances[msg.sender] += rewards;
        lastClaimTime[msg.sender] = block.timestamp;
    }
    
    function updateReputation(address account, uint newReputation) public {
        require(isAdmin[msg.sender] || isModerator[msg.sender], "Not authorized");
        reputation[account] = newReputation;
    }
    
    function setFeeRate(uint newFeeRate) public {
        require(isAdmin[msg.sender], "Not admin");
        feeRate = newFeeRate;
    }
    
    function setStakingPeriod(uint newPeriod) public {
        require(isAdmin[msg.sender], "Not admin");
        stakingPeriod = newPeriod;
    }
    
    function setRewardMultiplier(uint newMultiplier) public {
        require(isAdmin[msg.sender], "Not admin");
        rewardMultiplier = newMultiplier;
    }
    
    function setMinStakeAmount(uint newMin) public {
        require(isAdmin[msg.sender], "Not admin");
        minStakeAmount = newMin;
    }
    
    function setMaxStakeAmount(uint newMax) public {
        require(isAdmin[msg.sender], "Not admin");
        maxStakeAmount = newMax;
    }
    
    function emergencyPause() public {
        require(isAdmin[msg.sender], "Not admin");
        paused = true;
    }
    
    function emergencyUnpause() public {
        require(isAdmin[msg.sender], "Not admin");
        paused = false;
    }
    
    function mint(address to, uint amount) public {
        require(isAdmin[msg.sender], "Not admin");
        require(totalSupply + amount <= maxSupply, "Exceeds max supply");
        totalSupply += amount;
        balances[to] += amount;
    }
    
    function burn(uint amount) public {
        require(balances[msg.sender] >= amount, "Insufficient funds");
        totalSupply -= amount;
        balances[msg.sender] -= amount;
    }
}

// Example 2: Contract with no library usage (violates modularity)
contract NoLibraryContract {
    uint public balance;
    address public owner;
    
    function add(uint a, uint b) public pure returns (uint) {
        return a + b;
    }
    
    function subtract(uint a, uint b) public pure returns (uint) {
        return a - b;
    }
    
    function multiply(uint a, uint b) public pure returns (uint) {
        return a * b;
    }
    
    function divide(uint a, uint b) public pure returns (uint) {
        require(b != 0, "Division by zero");
        return a / b;
    }
    
    function modulo(uint a, uint b) public pure returns (uint) {
        require(b != 0, "Modulo by zero");
        return a % b;
    }
    
    function power(uint a, uint b) public pure returns (uint) {
        uint result = 1;
        for (uint i = 0; i < b; i++) {
            result *= a;
        }
        return result;
    }
    
    function sqrt(uint a) public pure returns (uint) {
        if (a == 0) return 0;
        uint z = (a + 1) / 2;
        uint y = a;
        while (z < y) {
            y = z;
            z = (a / z + z) / 2;
        }
        return y;
    }
    
    function isEven(uint a) public pure returns (bool) {
        return a % 2 == 0;
    }
    
    function isOdd(uint a) public pure returns (bool) {
        return a % 2 == 1;
    }
}

// Example 3: Contract with no inheritance (violates modularity)
contract NoInheritanceContract {
    uint public value;
    address public owner;
    bool public paused;
    
    function setValue(uint newValue) public {
        require(!paused, "Contract is paused");
        value = newValue;
    }
    
    function getValue() public view returns (uint) {
        return value;
    }
    
    function pause() public {
        require(msg.sender == owner, "Not owner");
        paused = true;
    }
    
    function unpause() public {
        require(msg.sender == owner, "Not owner");
        paused = false;
    }
    
    function transferOwnership(address newOwner) public {
        require(msg.sender == owner, "Not owner");
        owner = newOwner;
    }
    
    function emergencyWithdraw() public {
        require(msg.sender == owner, "Not owner");
        require(paused, "Not in emergency state");
        // Emergency withdrawal logic
    }
    
    function updateValue(uint newValue) public {
        require(msg.sender == owner, "Not owner");
        require(!paused, "Contract is paused");
        value = newValue;
    }
    
    function resetValue() public {
        require(msg.sender == owner, "Not owner");
        value = 0;
    }
    
    function getOwner() public view returns (address) {
        return owner;
    }
    
    function isPaused() public view returns (bool) {
        return paused;
    }
}
