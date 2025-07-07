pragma solidity ^0.8.0;

interface IDataFeed {
    function getData() external view returns (uint256);
}

contract SafeContract {
    IDataFeed public dataFeed;
    uint256 public lastData;

    constructor(IDataFeed _dataFeed) {
        dataFeed = _dataFeed;
    }

    function updateData() public {
        lastData = dataFeed.getData();
    }

    function currentData() public view returns (uint256) {
        // Returns the last updated data, not making an external call.
        return lastData;
    }
}


-