pragma solidity ^0.8.0;

// Using a Mock Oracle for price feed
contract PriceManipulationSafe {
    uint256 public price;

    function updatePrice(uint256 _price) public {
        //OnlyOwner
        price = _price;
    }

    function getPriceFromOracle() public view returns (uint256) {
        // Returns price from a trusted source (oracle)
        return price;
    }

    function calculateSomething(uint256 amount) public view returns (uint256 result){
        uint256 currentPrice = getPriceFromOracle();
        result = amount * currentPrice;
    }
}