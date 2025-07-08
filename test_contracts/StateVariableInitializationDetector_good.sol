pragma solidity ^0.8.0;

contract GoodContract {
    uint256 public x;
    address public owner;

    constructor() {
        owner = msg.sender; // 'owner' is initialized properly.
    }

    function setX(uint256 _x) public {
        x = _x;
    }
}