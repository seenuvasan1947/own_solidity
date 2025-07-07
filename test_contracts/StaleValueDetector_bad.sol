pragma solidity ^0.8.0;

interface IDataFeed {
    function getData() external view returns (uint256);
}

contract VulnerableContract {
    IDataFeed public dataFeed;
    uint256 public lastData;

    constructor(IDataFeed _dataFeed) {
        dataFeed = _dataFeed;
    }

    function updateData() public {
        lastData = dataFeed.getData();
    }

    function currentData() public view returns (uint256) {
        // This view function might return stale data if updateData() is called
        // and then currentData() is re-entered before updateData() completes
        return dataFeed.getData();
    }
}


-