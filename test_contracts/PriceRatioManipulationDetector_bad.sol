pragma solidity ^0.8.0;

interface IUniswapV2Pair {
    function getReserves() external view returns (uint112 reserve0, uint112 reserve1, uint32 blockTimestampLast);
    function token0() external view returns (address);
    function token1() external view returns (address);
}

contract PriceManipulationVulnerable {
    address public immutable uniswapV2Pair;

    constructor(address _uniswapV2Pair) {
        uniswapV2Pair = _uniswapV2Pair;
    }

    function getPriceDirect() public view returns (uint256 price) {
        IUniswapV2Pair pair = IUniswapV2Pair(uniswapV2Pair);
        (uint112 reserve0, uint112 reserve1, uint32 blockTimestampLast) = pair.getReserves();
        // Vulnerable: Directly using reserves for price calculation
        price = uint256(reserve1) / uint256(reserve0);
    }

    function calculateSomething(uint256 amount) public view returns (uint256 result){
        IUniswapV2Pair pair = IUniswapV2Pair(uniswapV2Pair);
         (uint112 reserve0, uint112 reserve1, uint32 blockTimestampLast) = pair.getReserves();
        result = amount * (uint256(reserve1) / uint256(reserve0));


    }
}