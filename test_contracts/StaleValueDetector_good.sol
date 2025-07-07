pragma solidity ^0.8.0;

interface ISafeDependency {
    function getValue() external view returns (uint256);
}

contract SafeContract {
    ISafeDependency public dependency;
    uint256 public myValue;

    constructor(ISafeDependency _dependency) {
        dependency = _dependency;
        myValue = 10;
    }

    function getValue() public view returns (uint256) {
        return myValue;
    }


    function getCombinedValue() public view returns (uint256) {
        return myValue + dependency.getValue();
    }

    function updateMyValue(uint256 _newValue) public {
        myValue = _newValue;
    }
}