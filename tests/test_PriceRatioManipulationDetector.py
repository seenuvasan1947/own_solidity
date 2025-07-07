import unittest
from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from rules.PriceRatioManipulationDetector import PriceRatioManipulationDetector

def run_rule_on_file(filepath, rule_class):
    input_stream = FileStream(filepath)
    lexer = SolidityLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = SolidityParser(stream)
    tree = parser.sourceUnit()

    rule_instance = rule_class()
    walker = ParseTreeWalker()
    walker.walk(rule_instance, tree)

    return rule_instance.get_violations()

class TestCommitRevealDetector(unittest.TestCase):
    def test_detects_vulnerability(self):
        violations = run_rule_on_file("test_contracts/PriceRatioManipulationDetector_bad.sol", PriceRatioManipulationDetector)
        self.assertTrue(any("Price calculated by ratio of token balances" in v for v in violations))

    def test_ignores_safe_contract(self):
        violations = run_rule_on_file("test_contracts/PriceRatioManipulationDetector_good.sol", PriceRatioManipulationDetector)
        self.assertEqual(len(violations), 0, f"Expected 0 violation, got: {violations}")

if __name__ == "__main__":
    # Create dummy files
    with open("test_contracts/PriceRatioManipulationDetector_bad.sol", "w") as f:
        f.write("""pragma solidity ^0.8.0;

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
""")

    with open("test_contracts/PriceRatioManipulationDetector_good.sol", "w") as f:
        f.write("""pragma solidity ^0.8.0;

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
""")

    unittest.main()