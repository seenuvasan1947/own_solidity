// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract OnlyContract {
    function isContract(address account) internal view returns (bool) {
        uint size;
        assembly { size := extcodesize(account) }
        return size > 0;
    }
    function risky(address to) public {
        require(isContract(msg.sender), "Only contracts allowed");
        // do something
    }
}
