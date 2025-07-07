pragma solidity ^0.8.0;

interface IUniswapV2Pair {
    function getReserves() external view returns (uint112 reserve0, uint112 reserve1, uint32 blockTimestampLast);
}

contract PriceManipulation {
    IUniswapV2Pair public immutable pair;

    constructor(address _pair) {
        pair = IUniswapV2Pair(_pair);
    }

    function getPrice() public view returns (uint) {
        (uint112 reserve0, uint112 reserve1, uint32 blockTimestampLast) = pair.getReserves();
        // Vulnerable: Directly using reserves for price calculation.
        return uint(reserve1) / uint(reserve0);
    }

    function exploit(uint amount) public {
        // In a real exploit, flash loans would be used here to manipulate reserves
        // to influence the price returned by `getPrice`.
    }
}