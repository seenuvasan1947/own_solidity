pragma solidity ^0.8.0;

// Vulnerable contract without emergency stop mechanism
contract NoEmergencyStop {
    address public owner;
    uint public criticalValue;
    mapping(address => uint) public balances;

    constructor() {
        owner = msg.sender;
    }

    // Critical function without emergency stop
    function updateCriticalValue(uint newValue) public {
        require(msg.sender == owner, "Only the owner can update this value");
        criticalValue = newValue;
    }

    function transfer(address to, uint amount) public {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        balances[msg.sender] -= amount;
        balances[to] += amount;
    }

    function withdraw(uint amount) public {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        balances[msg.sender] -= amount;
        payable(msg.sender).transfer(amount);
    }

    function mint(address to, uint amount) public {
        require(msg.sender == owner, "Only owner can mint");
        balances[to] += amount;
    }
}

// Contract with Pausable inheritance but critical functions don't use it
contract IncompletePausable {
    address public owner;
    uint public criticalValue;
    bool public paused;

    constructor() {
        owner = msg.sender;
    }

    modifier whenNotPaused() {
        require(!paused, "Contract is paused");
        _;
    }

    function pause() public {
        require(msg.sender == owner, "Only owner can pause");
        paused = true;
    }

    function unpause() public {
        require(msg.sender == owner, "Only owner can unpause");
        paused = false;
    }

    // Critical function without whenNotPaused modifier
    function updateCriticalValue(uint newValue) public {
        require(msg.sender == owner, "Only the owner can update this value");
        criticalValue = newValue;
    }

    function transfer(address to, uint amount) public {
        // Missing whenNotPaused modifier
        criticalValue = amount;
    }
}

// Secure contract with proper emergency stop mechanism
contract EmergencyStopExample {
    address public owner;
    uint public criticalValue;
    bool public paused;

    constructor() {
        owner = msg.sender;
    }

    modifier whenNotPaused() {
        require(!paused, "Contract is paused");
        _;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner");
        _;
    }

    function pause() public onlyOwner {
        paused = true;
    }

    function unpause() public onlyOwner {
        paused = false;
    }

    // Critical function with proper emergency stop
    function updateCriticalValue(uint newValue) public whenNotPaused onlyOwner {
        criticalValue = newValue;
    }

    function transfer(address to, uint amount) public whenNotPaused {
        criticalValue = amount;
    }

    function withdraw(uint amount) public whenNotPaused {
        criticalValue = amount;
    }
}

// Contract using OpenZeppelin Pausable pattern
contract OpenZeppelinPausable {
    address public owner;
    uint public criticalValue;
    bool private _paused;

    constructor() {
        owner = msg.sender;
    }

    modifier whenNotPaused() {
        require(!_paused, "Pausable: paused");
        _;
    }

    modifier whenPaused() {
        require(_paused, "Pausable: not paused");
        _;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Ownable: caller is not the owner");
        _;
    }

    function paused() public view virtual returns (bool) {
        return _paused;
    }

    function _pause() internal virtual whenNotPaused {
        _paused = true;
    }

    function _unpause() internal virtual whenPaused {
        _paused = false;
    }

    function pause() public virtual onlyOwner {
        _pause();
    }

    function unpause() public virtual onlyOwner {
        _unpause();
    }

    // Critical functions with proper pausable modifiers
    function updateCriticalValue(uint newValue) public whenNotPaused onlyOwner {
        criticalValue = newValue;
    }

    function mint(address to, uint amount) public whenNotPaused onlyOwner {
        criticalValue = amount;
    }

    function burn(uint amount) public whenNotPaused {
        criticalValue = amount;
    }
}

// Contract with emergency stop functions but no critical functions
contract OnlyEmergencyFunctions {
    address public owner;
    bool public paused;

    constructor() {
        owner = msg.sender;
    }

    modifier whenNotPaused() {
        require(!paused, "Contract is paused");
        _;
    }

    function pause() public {
        require(msg.sender == owner, "Only owner can pause");
        paused = true;
    }

    function unpause() public {
        require(msg.sender == owner, "Only owner can unpause");
        paused = false;
    }

    // Non-critical function
    function getValue() public view returns (uint) {
        return 42;
    }
}
