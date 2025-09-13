from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class UncaughtExceptionsDetector(SolidityParserListener):
    """
    Rule Code: 004
    Detects uncaught exceptions as defined in SCWE-004
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.current_function = None
        self.in_try_block = False
        self.try_block_depth = 0
        
    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"
        
    def exitContractDefinition(self, ctx):
        self.current_contract = None
        
    def enterFunctionDefinition(self, ctx):
        self.current_function = ctx.identifier().getText() if ctx.identifier() else "unknown"
        
    def exitFunctionDefinition(self, ctx):
        self.current_function = None
        
    def enterTryStatement(self, ctx):
        self.in_try_block = True
        self.try_block_depth += 1
        
    def exitTryStatement(self, ctx):
        self.try_block_depth -= 1
        if self.try_block_depth == 0:
            self.in_try_block = False
    
    def enterExpressionStatement(self, ctx):
        if not self.current_function:
            return
            
        expr_text = ctx.getText()
        
        # Rule 1: Check for unchecked low-level calls
        self._check_unchecked_calls(expr_text, ctx)
        
        # Rule 2: Check for incorrect use of assert() instead of require()
        self._check_wrong_assert_usage(expr_text, ctx)
        
        # Rule 3: Check for external calls without try/catch
        self._check_unprotected_external_calls(expr_text, ctx)
    
    def _check_unchecked_calls(self, expr_text, ctx):
        """Check for unchecked low-level calls that return boolean values"""
        # Patterns for low-level calls that return boolean
        unchecked_call_patterns = [
            'call(',
            'delegatecall(',
            'staticcall(',
            'send(',
            'transfer('  # transfer() can fail and should be checked
        ]
        
        for pattern in unchecked_call_patterns:
            if pattern in expr_text:
                # Check if the call is assigned to a variable or checked
                if not self._is_call_checked(expr_text, pattern):
                    line = ctx.start.line
                    self.violations.append(
                        f"❌ Uncaught exception in '{self.current_function}' of contract '{self.current_contract}' at line {line}: "
                        f"Low-level call '{pattern.strip('(')}' returns boolean but return value is not checked. "
                        f"Use require() to check success or assign to variable."
                    )
    
    def _check_wrong_assert_usage(self, expr_text, ctx):
        """Check for incorrect use of assert() instead of require()"""
        # Look for assert() statements that are used for input validation
        if 'assert(' in expr_text:
            # Common patterns where assert() should be require()
            input_validation_patterns = [
                'assert(amount',
                'assert(value',
                'assert(balance',
                'assert(msg.sender',
                'assert(owner',
                'assert(admin',
                'assert(amount >',
                'assert(amount >=',
                'assert(amount <',
                'assert(amount <=',
                'assert(value >',
                'assert(value >=',
                'assert(value <',
                'assert(value <=',
                'assert(balance >',
                'assert(balance >=',
                'assert(balance <',
                'assert(balance <=',
                'assert(msg.sender ==',
                'assert(msg.sender !=',
                'assert(owner ==',
                'assert(owner !=',
                'assert(admin ==',
                'assert(admin !='
            ]
            
            if any(pattern in expr_text for pattern in input_validation_patterns):
                line = ctx.start.line
                self.violations.append(
                    f"❌ Uncaught exception in '{self.current_function}' of contract '{self.current_contract}' at line {line}: "
                    f"Using assert() for input validation. Use require() instead for user input validation. "
                    f"assert() should only be used for invariants."
                )
    
    def _check_unprotected_external_calls(self, expr_text, ctx):
        """Check for external calls without try/catch protection"""
        if self.in_try_block:
            return  # Skip if we're already in a try block
            
        # Patterns for external contract calls
        external_call_patterns = [
            'ExternalContract(',
            'IERC20(',
            'IERC721(',
            'IERC1155(',
            'interface(',
            'contract(',
            'address(',
            'payable('
        ]
        
        # Check if this is an external call
        is_external_call = False
        for pattern in external_call_patterns:
            if pattern in expr_text:
                is_external_call = True
                break
        
        if is_external_call and not self._is_call_protected(expr_text):
            line = ctx.start.line
            self.violations.append(
                f"❌ Uncaught exception in '{self.current_function}' of contract '{self.current_contract}' at line {line}: "
                f"External contract call without try/catch protection. "
                f"Use try/catch blocks for external calls to handle potential failures."
            )
    
    def _is_call_checked(self, expr_text, pattern):
        """Check if a low-level call is properly checked"""
        # Check if the call is assigned to a variable
        if '=' in expr_text and pattern in expr_text:
            return True
        
        # Check if the call is wrapped in require()
        if 'require(' in expr_text and pattern in expr_text:
            return True
        
        # Check if the call is wrapped in if statement
        if 'if (' in expr_text and pattern in expr_text:
            return True
        
        return False
    
    def _is_call_protected(self, expr_text):
        """Check if an external call is protected with try/catch"""
        # This is a simplified check - in practice, you'd need more sophisticated parsing
        # to determine if the call is within a try block
        return False  # For now, we'll flag all external calls as unprotected
    
    def get_violations(self):
        return self.violations
