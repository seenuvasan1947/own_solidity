pragma solidity ^0.8.0;

interface IDex {
    function get_price() external view returns (uint);
}

contract VulnerableContract {
    IDex public dex;

    constructor(IDex _dex) {
        dex = _dex;
    }

    function calculateValue() public view returns (uint) {
        // Vulnerable: Directly using DEX spot price.
        uint price = dex.get_price();
        return price * 100;
    }
}