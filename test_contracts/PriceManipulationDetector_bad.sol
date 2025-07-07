pragma solidity ^0.8.0;

interface IDEX {
    function getPrice() external view returns (uint);
}

contract VulnerableContract {
    IDEX public dex;

    constructor(address _dex) {
        dex = IDEX(_dex);
    }

    function calculateValue() public view returns (uint) {
        // Directly using DEX spot price. Vulnerable to manipulation.
        uint price = dex.getPrice();
        return price * 100;
    }
}