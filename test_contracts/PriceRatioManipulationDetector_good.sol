pragma solidity ^0.8.0;

interface IDEX {
    function getReserves() external view returns (uint112 reserve0, uint112 reserve1, uint32 blockTimestampLast);
}

contract SafePriceCalculation {
    uint public lastPrice;

    function updatePrice(uint newPrice) public {
        lastPrice = newPrice;
    }

    function calculatePrice() public view returns (uint) {
        //Returning a stored price that is ideally sourced from a TWAP oracle
        return lastPrice;
    }
}