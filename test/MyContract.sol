pragma solidity ^0.8.0;

contract Test {
    function dangerous() public {
        address(this).call{value: 1 ether}("");
        address(this).delegatecall(abi.encodeWithSignature("doSomething()"));
    }

    function safe() public {
        payable(address(this)).transfer(1 ether);
    }
}

contract UnsafeContract {
    function kill() public {
        selfdestruct(payable(msg.sender));
    }

    function destroyIt() external {
        selfdestruct(payable(tx.origin));
    }
}