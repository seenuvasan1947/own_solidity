pragma solidity ^0.8.0;

contract BadContract {
    uint256 public x;
    address public owner; // 'owner' is not initialized, which may lead to issues.

    function setX(uint256 _x) public {
        x = _x;
    }
}