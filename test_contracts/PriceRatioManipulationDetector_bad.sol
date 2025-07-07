pragma solidity ^0.8.0;

interface IDEX {
    function getReserves() external view returns (uint112 reserve0, uint112 reserve1, uint32 blockTimestampLast);
}

contract PriceManipulation {
    IDEX public dex;

    constructor(address _dex) {
        dex = IDEX(_dex);
    }

    function calculatePrice() public view returns (uint) {
        (uint112 reserve0, uint112 reserve1, ) = dex.getReserves();
        require(reserve1 > 0, "Reserve1 cannot be zero");
        return reserve0 / reserve1;
    }
}