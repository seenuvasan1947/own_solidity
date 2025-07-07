pragma solidity ^0.8.0;

interface IDex {
    function getReserves() external view returns (uint112 reserve0, uint112 reserve1, uint32 blockTimestampLast);
    function getAmountsOut(uint amountIn, address[] memory path) external view returns (uint[] memory amounts);
}

contract PriceManipulation {
    IDex public dex;

    constructor(IDex _dex) {
        dex = _dex;
    }

    function calculatePrice() public view returns (uint) {
        (uint reserve0, uint reserve1,) = dex.getReserves();
        // Vulnerable: Calculating price directly from reserves
        return reserve0 / reserve1;
    }

    function calculatePricePath(uint amountIn, address[] memory path) public view returns (uint) {

        uint[] memory amounts = dex.getAmountsOut(amountIn,path);
        return amounts[amounts.length-1];

    }
}