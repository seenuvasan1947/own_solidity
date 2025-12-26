# S-ATR-002: Constant Functions Changing State
# Detects view/pure functions that modify state variables
# Based on Slither's const_functions_state detector
# Impact: MEDIUM | Confidence: MEDIUM

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class ConstantFunctionsStateDetector(SolidityParserListener):
    """
    Detects view/pure functions that change state variables.
    
    Vulnerability: Functions declared as view/pure should not modify state.
    Prior to Solidity 0.5, this wasn't enforced. From 0.5+, STATICCALL is used
    which reverts on state modification.
    
    Example (BAD):
        uint counter;
        function get() public view returns(uint) {
            counter = counter + 1;  // BAD: Modifies state in view function
            return counter;
        }
    
    Recommendation: Remove view/pure modifier if state modification is needed,
    or remove state-modifying code from view/pure functions.
    """
    
    def __init__(self):
        self.violations = []
        self.in_function = False
        self.function_name = None
        self.function_modifier = None
        self.function_line = None
        self.state_modifications = []
        self.current_contract = None
        self.state_variables = set()
    
    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.state_variables = set()
    
    def exitContractDefinition(self, ctx):
        self.current_contract = None
        self.state_variables = set()
    
    def enterStateVariableDeclaration(self, ctx):
        # Track state variables
        if ctx.identifier():
            var_name = ctx.identifier().getText()
            self.state_variables.add(var_name)
    
    def enterFunctionDefinition(self, ctx):
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.function_line = ctx.start.line
        self.function_modifier = None
        self.state_modifications = []
        
        # Check for view or pure modifiers
        for modifier in ctx.stateMutability():
            modifier_text = modifier.getText()
            if modifier_text in ["view", "pure"]:
                self.function_modifier = modifier_text
                break
    
    def exitFunctionDefinition(self, ctx):
        # Report if function is view/pure and modifies state
        if self.function_modifier and self.state_modifications:
            vars_str = ", ".join(self.state_modifications)
            self.violations.append(
                f"❌ [S-ATR-002] Function '{self.function_name}' at line {self.function_line} "
                f"is declared '{self.function_modifier}' but changes state variables: {vars_str}. "
                f"Remove the '{self.function_modifier}' modifier or remove state modifications."
            )
        
        self.in_function = False
        self.function_name = None
        self.function_modifier = None
        self.state_modifications = []
    
    def enterExpressionStatement(self, ctx):
        if not self.in_function or not self.function_modifier:
            return
        
        text = ctx.getText()
        
        # Check for assignments to state variables
        if "=" in text:
            # Simple heuristic: check if any state variable appears before '='
            for var in self.state_variables:
                if var in text and text.index(var) < text.index("="):
                    if var not in self.state_modifications:
                        self.state_modifications.append(var)
    
    def get_violations(self):
        return self.violations
