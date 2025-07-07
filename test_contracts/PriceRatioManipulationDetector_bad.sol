pragma solidity ^0.8.0;

interface IERC20 {
    function balanceOf(address account) external view returns (uint256);
}

contract PriceManipulationVulnerable {
    IERC20 public token0;
    IERC20 public token1;

    constructor(address _token0, address _token1) {
        token0 = IERC20(_token0);
        token1 = IERC20(_token1);
    }

    function getPrice() public view returns (uint256) {
        // Vulnerable: Price calculated directly from token balances
        uint256 balance0 = token0.balanceOf(address(this));
        uint256 balance1 = token1.balanceOf(address(this));
        return balance0 / balance1; // Vulnerable division!
    }
}