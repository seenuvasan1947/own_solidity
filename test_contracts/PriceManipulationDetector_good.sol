pragma solidity ^0.8.0;

// This is a simplified example and does not implement a real TWAP.
contract SafeContract {
    uint public lastPrice;
    uint public lastTimestamp;
    uint public twap;
    uint public period = 3600; // 1 hour

    function updatePrice(uint newPrice) public {
        uint currentTime = block.timestamp;
        if (lastTimestamp == 0) {
            lastPrice = newPrice;
            lastTimestamp = currentTime;
            twap = newPrice; // Initialize TWAP on first update
        } else {
            uint timeDelta = currentTime - lastTimestamp;
            if (timeDelta > period) {
                timeDelta = period;
            }

            //Simplified TWAP calculation (not production-ready)
            twap = (twap * (period - timeDelta) + newPrice * timeDelta) / period;
            lastPrice = newPrice;
            lastTimestamp = currentTime;
        }
    }

    function getPrice() public view returns (uint) {
        // Use TWAP instead of spot price
        return twap;
    }
}