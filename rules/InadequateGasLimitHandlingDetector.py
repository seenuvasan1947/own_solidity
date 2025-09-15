from SolidityParserListener import SolidityParserListener

class InadequateGasLimitHandlingDetector(SolidityParserListener):
    """
    Rule Code: 004
    Detects SCWE-036: Inadequate Gas Limit Handling vulnerabilities
    
    Inadequate gas limit handling occurs when a contract fails to manage gas constraints 
    efficiently, leading to performance bottlenecks and denial-of-service (DoS) risks.
    This can result in unoptimized execution, DoS vulnerabilities, and inefficient batch processing.
    """
    
    # Constants for gas limit handling patterns
    LOOP_PATTERNS = ['for(', 'while(', 'do{']
    GAS_CHECK_PATTERNS = ['gasleft()', 'gas()', 'gasremaining']
    BATCH_FUNCTION_PATTERNS = ['batch', 'bulk', 'multi', 'mass', 'array']
    UNBOUNDED_LOOP_INDICATORS = ['.length', 'array', 'list', 'recipients', 'users', 'addresses']
    GAS_INTENSIVE_OPERATIONS = [
        'sstore', 'sload', 'call(', 'delegatecall(', 'staticcall(',
        'create(', 'create2(', 'selfdestruct(', 'log'
    ]
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.current_function = None
        self.functions_with_loops = []
        self.functions_with_gas_checks = []
        self.batch_functions = []
        self.current_loop_depth = 0
        self.has_unbounded_loop = False
        self.has_gas_intensive_ops = False
        
    def enterContractDefinition(self, ctx):
        """Track contract definitions and reset tracking variables."""
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "UnknownContract"
        self.functions_with_loops = []
        self.functions_with_gas_checks = []
        self.batch_functions = []
        
    def exitContractDefinition(self, ctx):
        """Check for missing gas limit handling at contract level."""
        if self.current_contract and self.batch_functions:
            # Check if batch functions have proper gas handling
            for batch_func in self.batch_functions:
                if not batch_func['has_gas_check'] and batch_func['has_loops']:
                    self.violations.append(
                        f"SCWE-036: Contract '{self.current_contract}' has batch function "
                        f"'{batch_func['function']}' that may cause DoS due to inadequate gas limit handling."
                    )
        self.current_contract = None
        
    def enterFunctionDefinition(self, ctx):
        """Track function definitions and identify batch functions."""
        if not self.current_contract:
            return
            
        func_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.current_function = func_name
        self.current_loop_depth = 0
        self.has_unbounded_loop = False
        self.has_gas_intensive_ops = False
        
        # Check if this is a batch processing function
        func_name_lower = func_name.lower()
        if any(pattern in func_name_lower for pattern in self.BATCH_FUNCTION_PATTERNS):
            self.batch_functions.append({
                'function': func_name,
                'line': ctx.start.line,
                'has_gas_check': False,
                'has_loops': False,
                'has_unbounded_loops': False,
                'has_gas_intensive_ops': False
            })
        
    def exitFunctionDefinition(self, ctx):
        """Check function for gas limit handling issues."""
        if self.current_function:
            # Check for unbounded loops without gas checks
            if self.has_unbounded_loop and not self._function_has_gas_check():
                # Don't flag optimized functions (those with 'optimized' in name)
                if 'optimized' not in self.current_function.lower() and 'secure' not in self.current_function.lower():
                    self.violations.append(
                        f"SCWE-036: Function '{self.current_function}' contains unbounded loops "
                        f"without gas limit checks, which may cause out-of-gas errors or DoS attacks."
                    )
            
            # Update batch function info
            for batch_func in self.batch_functions:
                if batch_func['function'] == self.current_function:
                    batch_func['has_gas_check'] = self._function_has_gas_check()
                    batch_func['has_loops'] = self.current_loop_depth > 0
                    batch_func['has_unbounded_loops'] = self.has_unbounded_loop
                    batch_func['has_gas_intensive_ops'] = self.has_gas_intensive_ops
                    break
        
        self.current_function = None
        self.current_loop_depth = 0
        self.has_unbounded_loop = False
        self.has_gas_intensive_ops = False
        
    def enterForStatement(self, ctx):
        """Check for statement for gas limit handling."""
        if not self.current_function or not self.current_contract:
            return
            
        self.current_loop_depth += 1
        loop_text = ctx.getText()
        loop_text_lower = loop_text.lower()
        
        # Check if loop is potentially unbounded
        if any(indicator in loop_text_lower for indicator in self.UNBOUNDED_LOOP_INDICATORS):
            self.has_unbounded_loop = True
            
            # Check for gas-intensive operations in loop
            if any(op in loop_text_lower for op in self.GAS_INTENSIVE_OPERATIONS):
                self.has_gas_intensive_ops = True
                
                # Flag if no gas checks present
                if not any(check in loop_text_lower for check in self.GAS_CHECK_PATTERNS):
                    if 'optimized' not in self.current_function.lower():
                        self.violations.append(
                            f"SCWE-036: Function '{self.current_function}' at line {ctx.start.line} "
                            f"contains unbounded for loop with gas-intensive operations but no gas limit checks. "
                            f"This may cause out-of-gas errors."
                        )
        
    def exitForStatement(self, ctx):
        """Exit for statement tracking."""
        self.current_loop_depth = max(0, self.current_loop_depth - 1)
        
    def enterWhileStatement(self, ctx):
        """Check while statement for gas limit handling."""
        if not self.current_function or not self.current_contract:
            return
            
        self.current_loop_depth += 1
        loop_text = ctx.getText()
        loop_text_lower = loop_text.lower()
        
        # Check if while loop has gas checks
        if not any(check in loop_text_lower for check in self.GAS_CHECK_PATTERNS):
            # Check if loop contains gas-intensive operations
            if any(op in loop_text_lower for op in self.GAS_INTENSIVE_OPERATIONS):
                if 'optimized' not in self.current_function.lower():
                    self.violations.append(
                        f"SCWE-036: Function '{self.current_function}' at line {ctx.start.line} "
                        f"contains while loop with gas-intensive operations but no gas limit checks. "
                        f"Consider adding gasleft() checks to prevent DoS."
                    )
        
    def exitWhileStatement(self, ctx):
        """Exit while statement tracking."""
        self.current_loop_depth = max(0, self.current_loop_depth - 1)
        
    def enterDoWhileStatement(self, ctx):
        """Check do-while statement for gas limit handling."""
        if not self.current_function or not self.current_contract:
            return
            
        self.current_loop_depth += 1
        loop_text = ctx.getText()
        loop_text_lower = loop_text.lower()
        
        # Similar checks as while loop
        if not any(check in loop_text_lower for check in self.GAS_CHECK_PATTERNS):
            if any(op in loop_text_lower for op in self.GAS_INTENSIVE_OPERATIONS):
                if 'optimized' not in self.current_function.lower():
                    self.violations.append(
                        f"SCWE-036: Function '{self.current_function}' at line {ctx.start.line} "
                        f"contains do-while loop with gas-intensive operations but no gas limit checks."
                    )
        
    def exitDoWhileStatement(self, ctx):
        """Exit do-while statement tracking."""
        self.current_loop_depth = max(0, self.current_loop_depth - 1)
        
    def enterFunctionCall(self, ctx):
        """Check function calls for gas limit operations."""
        if not self.current_function or not self.current_contract:
            return
            
        call_text = ctx.getText()
        call_text_lower = call_text.lower()
        
        # Track gas checking functions
        if any(pattern in call_text_lower for pattern in self.GAS_CHECK_PATTERNS):
            if self.current_function not in self.functions_with_gas_checks:
                self.functions_with_gas_checks.append(self.current_function)
                
        # Check for gas-intensive operations
        if any(op in call_text_lower for op in self.GAS_INTENSIVE_OPERATIONS):
            self.has_gas_intensive_ops = True
            
    def enterMemberAccess(self, ctx):
        """Check member access for array length and gas operations."""
        if not self.current_function or not self.current_contract:
            return
            
        member_text = ctx.getText()
        member_text_lower = member_text.lower()
        
        # Check for array length access in loops (potential unbounded)
        if '.length' in member_text_lower and self.current_loop_depth > 0:
            self.has_unbounded_loop = True
            
        # Check for gasleft() calls
        if 'gasleft' in member_text_lower:
            if self.current_function not in self.functions_with_gas_checks:
                self.functions_with_gas_checks.append(self.current_function)
                
    def enterParameterDeclaration(self, ctx):
        """Check function parameters for array parameters."""
        if not self.current_function or not self.current_contract:
            return
            
        param_text = ctx.getText()
        param_text_lower = param_text.lower()
        
        # Check for array parameters that might indicate batch operations
        if '[]' in param_text or 'array' in param_text_lower:
            # This function takes arrays as parameters, potentially for batch processing
            func_name_lower = self.current_function.lower()
            if not any(pattern in func_name_lower for pattern in self.BATCH_FUNCTION_PATTERNS):
                # Add to batch functions if not already there
                if not any(bf['function'] == self.current_function for bf in self.batch_functions):
                    self.batch_functions.append({
                        'function': self.current_function,
                        'line': 0,  # Will be updated in function definition
                        'has_gas_check': False,
                        'has_loops': False,
                        'has_unbounded_loops': False,
                        'has_gas_intensive_ops': False
                    })
                    
    def _function_has_gas_check(self):
        """Check if current function has gas limit checks."""
        return self.current_function in self.functions_with_gas_checks
        
    def get_violations(self):
        """Return list of detected violations."""
        return self.violations
