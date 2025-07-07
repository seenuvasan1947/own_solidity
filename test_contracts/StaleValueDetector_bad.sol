pragma solidity ^0.8.0;

contract VulnerableContract {
    uint256 public value;
    address public otherContract;

    constructor(address _otherContract) {
        otherContract = _otherContract;
    }

    function setValue(uint256 _value) public {
        value = _value;
    }

    function getValue() public view returns (uint256) {
        // Simulate an external call that might modify state in another contract.
        // This is a simplified example; a real-world scenario would involve
        // a more complex interaction.
        IOtherContract(otherContract).modifyState();
        return value;
    }
}

interface IOtherContract {
    function modifyState() external;
}

contract OtherContract {
    uint256 public state;

    function modifyState() external {
        state = 123;
    }
}