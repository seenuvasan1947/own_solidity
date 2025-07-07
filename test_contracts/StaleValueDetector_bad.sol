pragma solidity ^0.8.0;

interface IBadDependency {
    function getValue() external view returns (uint256);
}

contract VulnerableContract {
    IBadDependency public dependency;
    uint256 public myValue;

    constructor(IBadDependency _dependency) {
        dependency = _dependency;
        myValue = 10;
    }

    function getStaleValue() public view returns (uint256) {
        uint256 externalValue = dependency.getValue(); // External call
        return myValue + externalValue; // Stale value because dependency might change myValue
    }

    function updateMyValue(uint256 _newValue) public {
        myValue = _newValue;
    }
}