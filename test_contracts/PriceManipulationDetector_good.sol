pragma solidity ^0.8.0;

interface IOracle {
    function getPrice() external view returns (uint);
}

contract SafeContract {
    IOracle public oracle;

    constructor(IOracle _oracle) {
        oracle = _oracle;
    }

    function calculateValue() public view returns (uint) {
        // Safe: Using price from a reliable oracle.
        uint price = oracle.getPrice();
        return price * 100;
    }
}