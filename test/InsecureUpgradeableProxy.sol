pragma solidity ^0.4.0;

// Vulnerable proxy contract - should be detected by SCWE-005 rule
contract VulnerableProxy {
    address public implementation;
    address public owner;

    // Vulnerable: No access control, no timelock
    function setImplementation(address _implementation) public {
        implementation = _implementation;
    }

    // Vulnerable: Public function without access control
    function upgrade(address _newImplementation) public {
        implementation = _newImplementation;
    }

    // Vulnerable: External function without proper controls
    function updateLogic(address _implementation) external {
        implementation = _implementation;
    }

    function() public payable {
        address _impl = implementation;
        require(_impl != address(0), "Implementation address is zero");
        assembly {
            let result := delegatecall(gas, _impl, add(msg.data, 0x20), mload(msg.data), 0, 0)
            let size := returndatasize
            let ptr := mload(0x40)
            return(ptr, size)
        }
    }
}

// Secure proxy contract - should NOT be detected
contract SecureProxy {
    address public implementation;
    address public owner;
    uint public lastUpgradeTime;
    uint public upgradeDelay = 1 days;

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can perform this action");
        _;
    }

    modifier upgradeable() {
        require(now >= lastUpgradeTime + upgradeDelay, "Upgrade not allowed yet");
        _;
    }

    // Secure: Has access control and timelock
    function setImplementation(address _implementation) public onlyOwner upgradeable {
        implementation = _implementation;
        lastUpgradeTime = now;
    }

    function() public payable {
        address _impl = implementation;
        require(_impl != address(0), "Implementation address is zero");
        assembly {
            let result := delegatecall(gas, _impl, add(msg.data, 0x20), mload(msg.data), 0, 0)
            let size := returndatasize
            let ptr := mload(0x40)
            return(ptr, size)
        }
    }
}
