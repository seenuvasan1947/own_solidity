pragma solidity ^0.4.0;

// Contract with deprecated usage - should be detected by SCWE-009 rule
contract DeprecatedUsage {
    address public owner;
    uint public balance;

    // Deprecated function usage
    function sendTransaction(address recipient, uint amount) public {
        recipient.transfer(amount); // Deprecated: direct transfer on address
    }
    
    function sendPayment(address recipient, uint amount) public {
        recipient.send(amount); // Deprecated: send() function
    }
    
    function useDeprecatedGlobals() public {
        uint currentTime = now; // Deprecated: now is deprecated
        // Using deprecated global variable
    }
    
    function useThrow() public {
        if (balance == 0) {
            throw; // Deprecated: throw is deprecated
        }
    }
    
    function useCallcode(address target, bytes data) public {
        target.callcode(data); // Deprecated: callcode is deprecated
    }
    
    function useSuicide() public {
        suicide(owner); // Deprecated: suicide is deprecated
    }
}

// Contract without deprecated usage - should NOT be detected
contract UpdatedUsage {
    address public owner;
    uint public balance;

    // Modern, non-deprecated usage
    function sendTransaction(address recipient, uint amount) public {
        payable(recipient).transfer(amount); // Modern approach
    }
    
    function sendPayment(address recipient, uint amount) public {
        (bool success, ) = recipient.call{value: amount}(""); // Modern approach
        require(success, "Transfer failed");
    }
    
    function useModernGlobals() public {
        uint currentTime = block.timestamp; // Modern: block.timestamp
        address sender = msg.sender; // Modern: explicit msg.sender
    }
    
    function useModernErrorHandling() public {
        require(balance > 0, "Insufficient balance"); // Modern: require
    }
    
    function useDelegatecall(address target, bytes data) public {
        (bool success, ) = target.delegatecall(data); // Modern: delegatecall
        require(success, "Delegatecall failed");
    }
    
    function useSelfdestruct() public {
        selfdestruct(payable(owner)); // Modern: selfdestruct
    }
}
