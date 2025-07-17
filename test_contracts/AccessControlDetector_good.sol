// Good: Has access control
contract GoodContract {
    address public owner;

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    function withdrawAll() public onlyOwner {
        // safe
    }

    function updateOwner(address newOwner) external onlyOwner {
        owner = newOwner;
    }
}
