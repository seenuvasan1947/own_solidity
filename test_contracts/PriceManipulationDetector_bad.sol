pragma solidity ^0.8.0;

interface IUniswapV2Router {
    function getAmountsOut(uint amountIn, address[] memory path) external view returns (uint[] memory amounts);
}

contract VulnerableContract {
    IUniswapV2Router public uniswapV2Router;
    address public tokenA;
    address public tokenB;

    constructor(address routerAddress, address _tokenA, address _tokenB) {
        uniswapV2Router = IUniswapV2Router(routerAddress);
        tokenA = _tokenA;
        tokenB = _tokenB;
    }

    function calculatePrice(uint amountIn) public view returns (uint) {
        address[] memory path = new address[](2);
        path[0] = tokenA;
        path[1] = tokenB;
        uint[] memory amounts = uniswapV2Router.getAmountsOut(amountIn, path);
        // Vulnerability: Directly using spot price from DEX
        return amounts[1];
    }
}