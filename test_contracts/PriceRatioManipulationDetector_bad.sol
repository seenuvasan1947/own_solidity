pragma solidity ^0.8.0;

contract PriceOracle {
    uint256 public tokenABalance;
    uint256 public tokenBBalance;

    constructor(uint256 _tokenABalance, uint256 _tokenBBalance) {
        tokenABalance = _tokenABalance;
        tokenBBalance = _tokenBBalance;
    }

    function getPrice() public view returns (uint256) {
        // Vulnerable: Price calculated by ratio of token balances
        return tokenABalance * 1e18 / tokenBBalance;
    }

    function updateBalances(uint256 _tokenABalance, uint256 _tokenBBalance) public {
        tokenABalance = _tokenABalance;
        tokenBBalance = _tokenBBalance;
    }
}