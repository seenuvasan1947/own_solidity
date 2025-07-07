pragma solidity ^0.8.0;

interface ERC20 {
    function balanceOf(address account) external view returns (uint256);
    function totalSupply() external view returns (uint256);
}

contract PriceManipulationVulnerable {
    ERC20 public token0;
    ERC20 public token1;

    constructor(address _token0, address _token1) {
        token0 = ERC20(_token0);
        token1 = ERC20(_token1);
    }

    function getPrice() public view returns (uint256) {
        // Vulnerable price calculation based on direct balance ratio.
        // A flash loan can manipulate these balances.
        uint256 balance0 = token0.balanceOf(address(this));
        uint256 balance1 = token1.balanceOf(address(this));
        return balance0 / balance1;
    }

    function getTotalSupplyRatio() public view returns (uint256) {
        // Vulnerable price calculation based on total supply ratio.
        // This is also prone to manipulation, though less common.
        uint256 supply0 = token0.totalSupply();
        uint256 supply1 = token1.totalSupply();
        return supply0 / supply1;
    }
}