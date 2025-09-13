// Test file for UncaughtExceptionsDetector
// This file contains examples of uncaught exceptions as defined in SCWE-004

pragma solidity ^0.8.0;

// Example 1: Unchecked low-level calls (violates exception handling)
contract UncheckedCall {
    function execute(address target, bytes memory data) public payable {
        //  No success check - will trigger violation
        target.call{value: msg.value}(data);
    }
    
    function sendEther(address payable recipient) public payable {
        //  No success check - will trigger violation
        recipient.send(msg.value);
    }
    
    function delegateCall(address target, bytes memory data) public {
        //  No success check - will trigger violation
        target.delegatecall(data);
    }
    
    function staticCall(address target, bytes memory data) public view {
        //  No success check - will trigger violation
        target.staticcall(data);
    }
    
    function transferEther(address payable recipient) public payable {
        //  No success check - will trigger violation
        recipient.transfer(msg.value);
    }
}

// Example 2: Wrong use of assert() instead of require() (violates exception handling)
contract WrongAssertion {
    function withdraw(uint256 amount) public {
        //  Assert should not be used for input validation - will trigger violation
        assert(amount > 0);
        // Withdraw logic here
    }
    
    function transfer(address to, uint256 amount) public {
        //  Assert should not be used for input validation - will trigger violation
        assert(amount > 0);
        assert(to != address(0));
        // Transfer logic here
    }
    
    function setOwner(address newOwner) public {
        //  Assert should not be used for input validation - will trigger violation
        assert(newOwner != address(0));
        assert(msg.sender == owner);
        // Set owner logic here
    }
    
    function updateBalance(uint256 newBalance) public {
        //  Assert should not be used for input validation - will trigger violation
        assert(newBalance >= 0);
        assert(msg.sender == admin);
        // Update balance logic here
    }
    
    function validateAmount(uint256 amount) public {
        //  Assert should not be used for input validation - will trigger violation
        assert(amount > 0);
        assert(amount <= 1000000);
        assert(amount % 100 == 0);
        // Validation logic here
    }
    
    address public owner;
    address public admin;
}

// Example 3: External calls without try/catch protection (violates exception handling)
interface ExternalContract {
    function riskyFunction() external;
    function anotherRiskyFunction() external returns (uint256);
    function transfer(address to, uint256 amount) external;
}

interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);
    function approve(address spender, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
}

contract NoErrorHandling {
    function callExternal(address contractAddr) public {
        //  No error handling - will trigger violation
        ExternalContract(contractAddr).riskyFunction();
    }
    
    function callExternalWithReturn(address contractAddr) public {
        //  No error handling - will trigger violation
        uint256 result = ExternalContract(contractAddr).anotherRiskyFunction();
        // Use result
    }
    
    function transferToken(address tokenAddr, address to, uint256 amount) public {
        //  No error handling - will trigger violation
        IERC20(tokenAddr).transfer(to, amount);
    }
    
    function approveToken(address tokenAddr, address spender, uint256 amount) public {
        //  No error handling - will trigger violation
        IERC20(tokenAddr).approve(spender, amount);
    }
    
    function transferFromToken(address tokenAddr, address from, address to, uint256 amount) public {
        //  No error handling - will trigger violation
        IERC20(tokenAddr).transferFrom(from, to, amount);
    }
    
    function multipleExternalCalls(address contract1, address contract2) public {
        //  No error handling - will trigger violation
        ExternalContract(contract1).riskyFunction();
        ExternalContract(contract2).riskyFunction();
    }
}

// Example 4: Mixed violations (multiple types of uncaught exceptions)
contract MixedViolations {
    address public owner;
    uint256 public balance;
    
    function complexFunction(address target, uint256 amount) public payable {
        //  Multiple violations in one function
        
        // Wrong assert usage
        assert(amount > 0);
        assert(msg.sender == owner);
        
        // Unchecked call
        target.call{value: msg.value}("");
        
        // External call without try/catch
        ExternalContract(target).riskyFunction();
        
        // Unchecked transfer
        payable(target).transfer(amount);
    }
    
    function anotherComplexFunction(address tokenAddr, address recipient, uint256 amount) public {
        //  Multiple violations in one function
        
        // Wrong assert usage
        assert(amount > 0);
        assert(recipient != address(0));
        
        // Unchecked external calls
        IERC20(tokenAddr).transfer(recipient, amount);
        IERC20(tokenAddr).approve(recipient, amount);
        
        // Unchecked delegatecall
        tokenAddr.delegatecall("");
    }
}

// Example 5: Correct implementations (should NOT trigger violations)
contract CorrectErrorHandling {
    address public owner;
    
    function execute(address target, bytes memory data) public payable {
        //  Properly checked call
        (bool success, bytes memory returnData) = target.call{value: msg.value}(data);
        require(success, "Call execution failed");
    }
    
    function withdraw(uint256 amount) public {
        //  Proper input validation with require
        require(amount > 0, "Invalid amount");
        require(msg.sender == owner, "Not owner");
        // Withdraw logic here
    }
    
    function callExternal(address contractAddr) public {
        //  Proper try/catch handling
        try ExternalContract(contractAddr).riskyFunction() {
            // Success case
        } catch {
            revert("External call failed");
        }
    }
    
    function transferToken(address tokenAddr, address to, uint256 amount) public {
        //  Proper try/catch handling
        try IERC20(tokenAddr).transfer(to, amount) returns (bool success) {
            require(success, "Token transfer failed");
        } catch {
            revert("Token transfer failed");
        }
    }
}
