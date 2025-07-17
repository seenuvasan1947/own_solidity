// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Parent {
    function exposed() public pure returns (uint) { return 1; }
    function internalLogic() internal pure returns (uint) { return 2; }
}
contract BadInheritance is Parent {
    // inherits Parent.exposed() as public with no override!
}
