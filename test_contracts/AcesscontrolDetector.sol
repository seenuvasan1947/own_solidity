contract Bank {
    address public owner;

    function withdrawAll() public {
        // No access control!
    }

    function emergencyWithdraw() external onlyOwner {
        // Safe
    }
}
