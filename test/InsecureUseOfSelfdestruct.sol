// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// Test contract for SCWE-038: Insecure Use of Selfdestruct
// This contract demonstrates vulnerable patterns in selfdestruct usage

contract InsecureSelfdestruct {
    uint256 public balance;
    
    // Vulnerable: No access control - anyone can destroy the contract
    function destroy() public {
        selfdestruct(payable(msg.sender)); // No access control
        // Critical vulnerability: Any user can destroy the contract
        // All funds will be sent to the caller
        // Contract becomes permanently inaccessible
    }
    
    // Vulnerable: Public selfdestruct with minimal checks
    function emergencyDestroy() public {
        require(balance == 0, "Balance must be zero");
        selfdestruct(payable(msg.sender));
        // Still vulnerable - anyone can call if balance is zero
        // No admin authorization required
    }
    
    // Vulnerable: Selfdestruct with weak authorization
    function adminDestroy(address admin) public {
        require(msg.sender == admin, "Not admin");
        selfdestruct(payable(admin));
        // Vulnerable: Admin address is provided by caller
        // Attacker can pass their own address as admin
    }
    
    // Vulnerable: Time-based destruction without proper controls
    function timedDestroy(uint256 timestamp) public {
        require(block.timestamp >= timestamp, "Too early");
        selfdestruct(payable(msg.sender));
        // Anyone can destroy after the timestamp
        // No admin verification
    }
    
    // Vulnerable: Conditional destruction with exploitable logic
    function conditionalDestroy(bool shouldDestroy) public {
        if (shouldDestroy) {
            selfdestruct(payable(msg.sender));
        }
        // Attacker can always pass true
        // No access control whatsoever
    }
}

contract SecureSelfdestruct {
    address public admin;
    bool public paused = false;
    uint256 public destructionDelay = 7 days;
    uint256 public destructionRequestTime;
    bool public destructionRequested = false;

    constructor(address _admin) {
        admin = _admin;
    }

    modifier onlyAdmin() {
        require(msg.sender == admin, "Unauthorized");
        _;
    }
    
    modifier whenNotPaused() {
        require(!paused, "Contract is paused");
        _;
    }
    
    modifier circuitBreaker() {
        require(!paused, "Emergency stop activated");
        _;
    }

    // Secure: Proper access control with admin restriction
    function destroy() public onlyAdmin {
        selfdestruct(payable(admin)); // Restricted to admin
        // Only the designated admin can destroy the contract
        // Funds go to the verified admin address
    }
    
    // Secure: Two-step destruction with time delay
    function requestDestruction() public onlyAdmin whenNotPaused {
        destructionRequested = true;
        destructionRequestTime = block.timestamp;
        // Admin must first request destruction
        // Introduces time delay for security
    }
    
    function executeDestruction() public onlyAdmin {
        require(destructionRequested, "Destruction not requested");
        require(block.timestamp >= destructionRequestTime + destructionDelay, "Delay period not met");
        
        selfdestruct(payable(admin));
        // Two-step process with time delay
        // Gives time to detect and prevent malicious destruction
    }
    
    // Secure: Emergency pause mechanism
    function pause() public onlyAdmin {
        paused = true;
        // Admin can pause contract in emergency
        // Prevents destruction when suspicious activity detected
    }
    
    function unpause() public onlyAdmin {
        paused = false;
    }
    
    // Secure: Circuit breaker protected destruction
    function emergencyDestroy() public onlyAdmin circuitBreaker {
        require(address(this).balance == 0, "Contract must be empty");
        selfdestruct(payable(admin));
        // Multiple layers of protection:
        // 1. Admin only access
        // 2. Circuit breaker check
        // 3. Empty balance requirement
    }
    
    // Secure: Multi-signature style destruction (simplified)
    mapping(address => bool) public authorizedAdmins;
    mapping(bytes32 => uint256) public destructionVotes;
    uint256 public constant REQUIRED_VOTES = 2;
    
    function addAuthorizedAdmin(address newAdmin) public onlyAdmin {
        authorizedAdmins[newAdmin] = true;
    }
    
    function voteForDestruction(bytes32 destructionId) public {
        require(authorizedAdmins[msg.sender], "Not authorized");
        destructionVotes[destructionId]++;
    }
    
    function executeMultisigDestruction(bytes32 destructionId) public {
        require(authorizedAdmins[msg.sender], "Not authorized");
        require(destructionVotes[destructionId] >= REQUIRED_VOTES, "Insufficient votes");
        
        selfdestruct(payable(admin));
        // Multi-signature approach for critical operations
        // Requires multiple authorized parties to agree
    }
    
    // Admin management functions
    function transferAdmin(address newAdmin) public onlyAdmin {
        require(newAdmin != address(0), "Invalid address");
        admin = newAdmin;
    }
}

contract TimeLockedSelfdestruct {
    address public owner;
    uint256 public constant TIMELOCK_DELAY = 48 hours;
    uint256 public destructionUnlockTime;
    bool public destructionScheduled = false;
    
    constructor() {
        owner = msg.sender;
    }
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }
    
    // Secure: Time-locked destruction scheduling
    function scheduleDestruction() public onlyOwner {
        destructionUnlockTime = block.timestamp + TIMELOCK_DELAY;
        destructionScheduled = true;
        // Owner schedules destruction with mandatory delay
        // Provides time window for intervention
    }
    
    function cancelDestruction() public onlyOwner {
        destructionScheduled = false;
        destructionUnlockTime = 0;
        // Owner can cancel scheduled destruction
        // Safety mechanism against accidental scheduling
    }
    
    function executeScheduledDestruction() public onlyOwner {
        require(destructionScheduled, "Destruction not scheduled");
        require(block.timestamp >= destructionUnlockTime, "Timelock not expired");
        
        selfdestruct(payable(owner));
        // Time-locked execution provides security delay
        // Prevents hasty or malicious destruction
    }
}
