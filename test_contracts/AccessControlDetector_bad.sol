// Bad: No access control
contract BadContract {
    function withdrawAll() public {
        // dangerous
    }

    function updateOwner(address newOwner) external {
        // anyone can call this
    }
}
