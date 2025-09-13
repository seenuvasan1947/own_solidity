// Test file for ExcessiveContractComplexityDetector
// This file contains examples of excessive contract complexity as defined in SCWE-002

pragma solidity ^0.8.0;

// Example 1: Contract with too many functions (violates function count threshold)
contract ExcessiveFunctionsContract {
    uint public balance;
    address public owner;
    uint public value1;
    uint public value2;
    uint public value3;
    uint public value4;
    uint public value5;
    
    // Too many functions - this will trigger the violation
    function func1() public { balance += 1; }
    function func2() public { balance += 2; }
    function func3() public { balance += 3; }
    function func4() public { balance += 4; }
    function func5() public { balance += 5; }
    function func6() public { balance += 6; }
    function func7() public { balance += 7; }
    function func8() public { balance += 8; }
    function func9() public { balance += 9; }
    function func10() public { balance += 10; }
    function func11() public { balance += 11; }
    function func12() public { balance += 12; }
    function func13() public { balance += 13; }
    function func14() public { balance += 14; }
    function func15() public { balance += 15; }
    function func16() public { balance += 16; }
    function func17() public { balance += 17; }
    function func18() public { balance += 18; }
    function func19() public { balance += 19; }
    function func20() public { balance += 20; }
    function func21() public { balance += 21; } // This makes it 21 functions
    function func22() public { balance += 22; }
    function func23() public { balance += 23; }
}

// Example 2: Contract with excessive function complexity
contract ComplexFunctionContract {
    uint public balance;
    address public owner;
    
    // Function with too many conditions and nesting
    function complexFunction(uint value) public {
        // Too many conditions - will trigger violation
        if (value > 10) {
            if (value > 20) {
                if (value > 30) {
                    if (value > 40) {
                        if (value > 50) {
                            if (value > 60) {
                                if (value > 70) {
                                    if (value > 80) {
                                        if (value > 90) {
                                            if (value > 100) {
                                                if (value > 110) { // 11th condition
                                                    balance += value;
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        
        // Too many loops - will trigger violation
        for (uint i = 0; i < 10; i++) {
            for (uint j = 0; j < 10; j++) {
                for (uint k = 0; k < 10; k++) {
                    for (uint l = 0; l < 10; l++) {
                        for (uint m = 0; m < 10; m++) {
                            for (uint n = 0; n < 10; n++) { // 6th loop
                                balance += i + j + k + l + m + n;
                            }
                        }
                    }
                }
            }
        }
    }
}

// Example 3: Contract with deep inheritance (will trigger inheritance depth violation)
contract BaseContract {
    uint public baseValue;
}

contract Level1Contract is BaseContract {
    uint public level1Value;
}

contract Level2Contract is Level1Contract {
    uint public level2Value;
}

contract Level3Contract is Level2Contract {
    uint public level3Value;
}

contract Level4Contract is Level3Contract { // 4 levels of inheritance - will trigger violation
    uint public level4Value;
}

// Example 4: Contract with very long function (will trigger line count violation)
contract LongFunctionContract {
    uint public balance;
    
    function veryLongFunction(uint value) public {
        // This function is intentionally long to trigger the line count violation
        balance += value;
        balance += value;
        balance += value;
        balance += value;
        balance += value;
        balance += value;
        balance += value;
        balance += value;
        balance += value;
        balance += value;
        balance += value;
        balance += value;
        balance += value;
        balance += value;
        balance += value;
        balance += value;
        balance += value;
        balance += value;
        balance += value;
        balance += value;
        balance += value;
        balance += value;
        balance += value;
        balance += value;
        balance += value;
        balance += value;
        balance += value;
        balance += value;
        balance += value;
        balance += value;
        balance += value;
        balance += value;
        balance += value;
        balance += value;
        balance += value;
        balance += value;
        balance += value;
        balance += value;
        balance += value;
        balance += value;
        balance += value;
        balance += value;
        balance += value;
        balance += value;
        balance += value;
        balance += value;
        balance += value;
        balance += value;
        balance += value;
        balance += value; // This should make it over 50 lines
    }
}
