pragma solidity ^0.8.0;

// Contract with lack of multisig governance - should be detected by SCWE-012 rule
contract CentralizedGovernance {
    address public owner;
    address public admin;
    uint256 public totalFunds;

    constructor() {
        owner = msg.sender;
        admin = msg.sender;
    }

    // Critical function with single owner check - should be flagged
    function upgradeContract(address newContract) public {
        require(msg.sender == owner, "Only owner can upgrade");
        // Single point of failure
    }

    // Critical function with single owner check - should be flagged
    function withdrawFunds(address payable recipient, uint256 amount) public {
        require(msg.sender == owner, "Only owner can withdraw funds");
        recipient.transfer(amount);
    }

    // Critical function with admin check - should be flagged
    function setFee(uint256 newFee) public {
        require(msg.sender == admin, "Only admin can set fee");
        // Single point of failure
    }

    // Critical function without any access control - should be flagged
    function emergencyWithdraw() public {
        // No access control at all
        payable(owner).transfer(address(this).balance);
    }

    // Critical function with owner check - should be flagged
    function pauseContract() public {
        require(msg.sender == owner, "Only owner can pause");
        // Single point of failure
    }

    // Critical function with owner check - should be flagged
    function mintTokens(address to, uint256 amount) public {
        require(msg.sender == owner, "Only owner can mint");
        // Single point of failure
    }
}

// Contract with proper multisig governance - should NOT be detected
contract SecureGovernance {
    address public multisigWallet;
    uint256 public totalFunds;

    constructor(address _multisigWallet) {
        multisigWallet = _multisigWallet;
    }

    // Critical function with multisig governance - should NOT be flagged
    function upgradeContract(address newContract) public {
        require(msg.sender == multisigWallet, "Only multisig can upgrade");
        // Proper multisig governance
    }

    // Critical function with multisig governance - should NOT be flagged
    function withdrawFunds(address payable recipient, uint256 amount) public {
        require(msg.sender == multisigWallet, "Only multisig can withdraw");
        recipient.transfer(amount);
    }

    // Critical function with multisig governance - should NOT be flagged
    function setFee(uint256 newFee) public {
        require(msg.sender == multisigWallet, "Only multisig can set fee");
        // Proper multisig governance
    }
}

// Contract inheriting from multisig contract - should NOT be detected
interface IMultiSig {
    function submitTransaction(address destination, uint256 value, bytes calldata data) external;
}

contract MultisigInheritance is IMultiSig {
    address public owner;
    IMultiSig public multisig;

    constructor(address _multisig) {
        multisig = IMultiSig(_multisig);
    }

    // Critical function using multisig interface - should NOT be flagged
    function upgradeContract(address newContract) public {
        bytes memory data = abi.encodeWithSignature("upgradeTo(address)", newContract);
        multisig.submitTransaction(address(this), 0, data);
    }

    // Critical function using multisig interface - should NOT be flagged
    function withdrawFunds(address payable recipient, uint256 amount) public {
        bytes memory data = abi.encodeWithSignature("transfer(address,uint256)", recipient, amount);
        multisig.submitTransaction(address(this), 0, data);
    }
}

// Contract with timelock governance - should NOT be detected
contract TimelockGovernance {
    address public timelock;
    uint256 public totalFunds;

    constructor(address _timelock) {
        timelock = _timelock;
    }

    // Critical function with timelock governance - should NOT be flagged
    function upgradeContract(address newContract) public {
        require(msg.sender == timelock, "Only timelock can upgrade");
        // Proper timelock governance
    }

    // Critical function with timelock governance - should NOT be flagged
    function setParameter(uint256 newValue) public {
        require(msg.sender == timelock, "Only timelock can set parameter");
        // Proper timelock governance
    }
}

// Contract with DAO governance - should NOT be detected
contract DAOGovernance {
    address public dao;
    uint256 public totalFunds;

    constructor(address _dao) {
        dao = _dao;
    }

    // Critical function with DAO governance - should NOT be flagged
    function upgradeContract(address newContract) public {
        require(msg.sender == dao, "Only DAO can upgrade");
        // Proper DAO governance
    }

    // Critical function with DAO governance - should NOT be flagged
    function withdrawFunds(address payable recipient, uint256 amount) public {
        require(msg.sender == dao, "Only DAO can withdraw");
        recipient.transfer(amount);
    }
}
