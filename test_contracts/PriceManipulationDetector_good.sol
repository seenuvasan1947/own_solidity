pragma solidity ^0.8.0;

interface IOracle {
    function getPrice() external view returns (uint);
}

contract SafeContract {
    IOracle public oracle;

    constructor(address _oracle) {
        oracle = IOracle(_oracle);
    }

    function calculateValue() public view returns (uint) {
        // Using an oracle for price feed.
        uint price = oracle.getPrice();
        return price * 100;
    }
}