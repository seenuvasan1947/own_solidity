// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// Test contract for SCWE-037: Insufficient Protection Against Front-Running
// This contract demonstrates vulnerable patterns in front-running protection

interface IERC20 {
    function transferFrom(address sender, address recipient, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

contract FrontRunningVulnerable {
    IERC20 public token;
    uint256 public price = 1 ether; // 1 token = 1 ETH

    constructor(address _token) {
        token = IERC20(_token);
    }

    // Vulnerable: No front-running protection
    function buyTokens(uint256 amount) public payable {
        require(msg.value >= amount * price, "Insufficient ETH");
        token.transferFrom(address(this), msg.sender, amount);
        // Attackers see the transaction in the mempool and execute a transaction to buy first
        // Victim's transaction executes at a higher price or fails due to slippage
        // Attacker sells at a profit, exploiting sandwich attacks
    }
    
    // Vulnerable: Simple trading without protection
    function sellTokens(uint256 amount) public {
        require(token.balanceOf(msg.sender) >= amount, "Insufficient tokens");
        token.transferFrom(msg.sender, address(this), amount);
        payable(msg.sender).transfer(amount * price);
        // No slippage protection, no deadline, vulnerable to front-running
    }
    
    // Vulnerable: Auction without commit-reveal
    function placeBid(uint256 amount) public payable {
        require(msg.value >= amount, "Insufficient payment");
        // Bid is visible in mempool, can be front-run
        // No commit-reveal scheme to hide bid amount
    }
    
    // Vulnerable: Price-sensitive swap without protection
    function swapTokens(address tokenA, address tokenB, uint256 amountIn) public {
        // No slippage protection
        // No deadline check
        // No minimum received amount
        // Vulnerable to sandwich attacks
    }
    
    // Vulnerable: Order execution without safeguards
    function executeOrder(uint256 amount, uint256 targetPrice) public {
        require(price <= targetPrice, "Price too high");
        // No deadline check - order can be delayed
        // No slippage tolerance
        // Front-runners can manipulate price before execution
    }
}

contract SecureTrade {
    IERC20 public token;
    mapping(address => bytes32) public commitments;
    mapping(address => uint256) public commitTimestamps;
    uint256 public price = 1 ether;
    uint256 public constant REVEAL_DELAY = 1 hours;

    constructor(address _token) {
        token = IERC20(_token);
    }

    // Secure: Commit-reveal scheme to hide trade intent
    function commitTrade(bytes32 hash) public {
        commitments[msg.sender] = hash;
        commitTimestamps[msg.sender] = block.timestamp;
    }

    function executeTrade(uint256 amount, bytes32 secret) public payable {
        require(commitments[msg.sender] == keccak256(abi.encodePacked(amount, secret)), "Invalid commitment");
        require(block.timestamp >= commitTimestamps[msg.sender] + REVEAL_DELAY, "Too early to reveal");
        require(msg.value >= amount * price, "Insufficient ETH");
        
        commitments[msg.sender] = 0; // Prevent reusing commitment
        token.transferFrom(address(this), msg.sender, amount);
        // Traders commit to the trade off-chain before revealing the amount
        // Transactions cannot be front-run because attackers don't know the amount until revealed
    }
    
    // Secure: Trading with slippage protection
    function buyTokensSecure(
        uint256 amount, 
        uint256 maxPrice,
        uint256 deadline
    ) public payable {
        require(block.timestamp <= deadline, "Transaction expired");
        require(price <= maxPrice, "Price exceeds slippage tolerance");
        require(msg.value >= amount * price, "Insufficient ETH");
        
        token.transferFrom(address(this), msg.sender, amount);
    }
    
    // Secure: Swap with comprehensive protection
    function swapTokensSecure(
        address tokenA,
        address tokenB, 
        uint256 amountIn,
        uint256 minAmountOut,
        uint256 deadline
    ) public {
        require(block.timestamp <= deadline, "Swap expired");
        // minAmountOut provides slippage protection
        // deadline prevents delayed execution
        // Protected against sandwich attacks
    }
    
    // Secure: Auction with commit-reveal
    function commitBid(bytes32 bidCommitment) public {
        commitments[msg.sender] = bidCommitment;
        commitTimestamps[msg.sender] = block.timestamp;
    }
    
    function revealBid(uint256 amount, bytes32 nonce) public payable {
        require(block.timestamp >= commitTimestamps[msg.sender] + REVEAL_DELAY, "Reveal period not started");
        require(commitments[msg.sender] == keccak256(abi.encodePacked(amount, nonce)), "Invalid bid commitment");
        require(msg.value >= amount, "Insufficient payment");
        
        commitments[msg.sender] = 0;
        // Bid amount was hidden during commit phase
        // Front-runners couldn't see the actual bid amount
    }
}

contract TimeDelayProtection {
    mapping(address => uint256) public orderTimestamps;
    uint256 public constant ORDER_DELAY = 30 minutes;
    
    // Secure: Time delay protection
    function placeOrder(uint256 amount) public {
        orderTimestamps[msg.sender] = block.timestamp;
        // Order placement with time delay
    }
    
    function executeOrderWithDelay(uint256 amount) public {
        require(block.timestamp >= orderTimestamps[msg.sender] + ORDER_DELAY, "Order still in delay period");
        // Time delay reduces front-running opportunities
        // Gives time for price stabilization
    }
}
