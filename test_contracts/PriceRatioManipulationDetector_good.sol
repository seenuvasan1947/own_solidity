pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@chainlink/contracts/src/v0.8/interfaces/AggregatorV3Interface.sol";

contract PriceFeedConsumer {
    AggregatorV3Interface internal priceFeed;

    /**
     * Network: Sepolia
     * Aggregator: ETH / USD
     * Address: 0x694AA17696899952f4E0cbd354cB470de8E5a030
     */
    constructor() {
        priceFeed = AggregatorV3Interface(0x694AA17696899952f4E0cbd354cB470de8E5a030);
    }

    /**
     * Returns the latest ETH / USD price
     */
    function getLatestPrice() public view returns (int) {
        (, int price, , , ) = priceFeed.latestRoundData();
        return price;
    }
}