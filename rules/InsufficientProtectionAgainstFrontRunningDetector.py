from SolidityParserListener import SolidityParserListener

class InsufficientProtectionAgainstFrontRunningDetector(SolidityParserListener):
    """
    Rule Code: 005
    Detects SCWE-037: Insufficient Protection Against Front-Running vulnerabilities
    
    Insufficient protection against front-running refers to vulnerabilities that allow 
    malicious actors to exploit the order of transactions for profit. This can lead to 
    unauthorized actions by malicious actors, loss of funds or data, and exploitation 
    of the contract's logic.
    """
    
    # Constants for front-running protection patterns
    TRADING_FUNCTION_PATTERNS = [
        'buy', 'sell', 'trade', 'swap', 'exchange', 'purchase', 'order', 'bid', 'auction'
    ]
    
    PRICE_RELATED_PATTERNS = ['price', 'rate', 'amount', 'value', 'cost', 'fee']
    
    COMMIT_REVEAL_PATTERNS = [
        'commit', 'reveal', 'commitment', 'hash', 'secret', 'nonce'
    ]
    
    TIME_DELAY_PATTERNS = [
        'delay', 'timelock', 'cooldown', 'waiting', 'period', 'timestamp'
    ]
    
    FRONT_RUNNING_PROTECTION_PATTERNS = [
        'slippage', 'deadline', 'minreceived', 'maxpaid', 'tolerance'
    ]
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.current_function = None
        self.trading_functions = []
        self.has_commit_reveal = False
        self.has_time_delays = False
        self.has_slippage_protection = False
        self.commitment_mappings = []
        
    def enterContractDefinition(self, ctx):
        """Track contract definitions and reset tracking variables."""
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "UnknownContract"
        self.trading_functions = []
        self.has_commit_reveal = False
        self.has_time_delays = False
        self.has_slippage_protection = False
        self.commitment_mappings = []
        
    def exitContractDefinition(self, ctx):
        """Check for missing front-running protection at contract level."""
        if self.current_contract and self.trading_functions:
            # Check if trading contract has any protection mechanisms
            if not self.has_commit_reveal and not self.has_time_delays and not self.has_slippage_protection:
                if 'secure' not in self.current_contract.lower():
                    self.violations.append(
                        f"SCWE-037: Contract '{self.current_contract}' contains trading functions "
                        f"but lacks front-running protection mechanisms (commit-reveal, time delays, or slippage protection)."
                    )
        self.current_contract = None
        
    def enterFunctionDefinition(self, ctx):
        """Track function definitions and identify trading functions."""
        if not self.current_contract:
            return
            
        func_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.current_function = func_name
        
        # Check if this is a trading function
        func_name_lower = func_name.lower()
        if any(pattern in func_name_lower for pattern in self.TRADING_FUNCTION_PATTERNS):
            # Don't track secure functions as vulnerable
            if 'secure' not in func_name_lower and 'protected' not in func_name_lower:
                self.trading_functions.append({
                    'function': func_name,
                    'line': ctx.start.line,
                    'has_commit_reveal': False,
                    'has_time_delay': False,
                    'has_slippage_protection': False,
                    'has_deadline_check': False,
                    'vulnerable': True
                })
        
    def exitFunctionDefinition(self, ctx):
        """Check trading functions for front-running vulnerabilities."""
        if self.current_function and self.trading_functions:
            # Find current function in trading_functions
            current_func_info = None
            for func_info in self.trading_functions:
                if func_info['function'] == self.current_function:
                    current_func_info = func_info
                    break
                    
            if current_func_info and current_func_info['vulnerable']:
                # Don't flag secure functions
                if 'secure' not in self.current_function.lower():
                    # Check for missing protection mechanisms
                    if not current_func_info['has_commit_reveal']:
                        self.violations.append(
                            f"SCWE-037: Trading function '{self.current_function}' at line {current_func_info['line']} "
                            f"lacks commit-reveal scheme protection against front-running attacks."
                        )
                        
                    if not current_func_info['has_slippage_protection']:
                        self.violations.append(
                            f"SCWE-037: Trading function '{self.current_function}' at line {current_func_info['line']} "
                            f"lacks slippage protection, making it vulnerable to sandwich attacks."
                        )
                        
                    if not current_func_info['has_deadline_check']:
                        self.violations.append(
                            f"SCWE-037: Trading function '{self.current_function}' at line {current_func_info['line']} "
                            f"lacks deadline checks, allowing transactions to be delayed and exploited."
                        )
        
        self.current_function = None
        
    def enterStateVariableDeclaration(self, ctx):
        """Check for front-running protection related state variables."""
        if not self.current_contract:
            return
            
        var_name = ctx.identifier().getText() if ctx.identifier() else ""
        var_name_lower = var_name.lower()
        var_text = ctx.getText().lower()
        
        # Check for commitment mappings (commit-reveal scheme)
        if any(pattern in var_name_lower for pattern in self.COMMIT_REVEAL_PATTERNS):
            if 'mapping' in var_text:
                self.commitment_mappings.append(var_name)
                self.has_commit_reveal = True
                
        # Check for time delay related variables
        if any(pattern in var_name_lower for pattern in self.TIME_DELAY_PATTERNS):
            self.has_time_delays = True
            
        # Check for slippage protection variables
        if any(pattern in var_name_lower for pattern in self.FRONT_RUNNING_PROTECTION_PATTERNS):
            self.has_slippage_protection = True
            
    def enterParameterDeclaration(self, ctx):
        """Check function parameters for front-running protection."""
        if not self.current_function or not self.current_contract:
            return
            
        param_name = ctx.identifier().getText() if ctx.identifier() else ""
        param_name_lower = param_name.lower()
        
        # Update current trading function info
        for func_info in self.trading_functions:
            if func_info['function'] == self.current_function:
                # Check for slippage protection parameters
                if any(pattern in param_name_lower for pattern in self.FRONT_RUNNING_PROTECTION_PATTERNS):
                    func_info['has_slippage_protection'] = True
                    
                # Check for deadline parameters
                if 'deadline' in param_name_lower or 'timeout' in param_name_lower:
                    func_info['has_deadline_check'] = True
                    
                # Check for commit-reveal parameters
                if any(pattern in param_name_lower for pattern in self.COMMIT_REVEAL_PATTERNS):
                    func_info['has_commit_reveal'] = True
                break
                
    def enterRequireStatement(self, ctx):
        """Check require statements for front-running protection."""
        if not self.current_function or not self.current_contract:
            return
            
        require_text = ctx.getText()
        require_text_lower = require_text.lower()
        
        # Update current trading function info
        for func_info in self.trading_functions:
            if func_info['function'] == self.current_function:
                # Check for slippage protection in require statements
                if any(pattern in require_text_lower for pattern in self.FRONT_RUNNING_PROTECTION_PATTERNS):
                    func_info['has_slippage_protection'] = True
                    
                # Check for deadline checks
                if 'deadline' in require_text_lower or 'block.timestamp' in require_text_lower:
                    func_info['has_deadline_check'] = True
                    
                # Check for commitment verification
                if any(pattern in require_text_lower for pattern in self.COMMIT_REVEAL_PATTERNS):
                    func_info['has_commit_reveal'] = True
                    
                # If function has any protection, mark as not vulnerable
                if (func_info['has_commit_reveal'] or func_info['has_slippage_protection'] or 
                    func_info['has_deadline_check']):
                    func_info['vulnerable'] = False
                break
                
    def enterExpressionStatement(self, ctx):
        """Check expression statements for require calls with protection."""
        if not self.current_function or not self.current_contract:
            return
            
        expr_text = ctx.getText()
        expr_text_lower = expr_text.lower()
        
        # Check for require statements with protection
        if 'require(' in expr_text_lower:
            # Update current trading function info
            for func_info in self.trading_functions:
                if func_info['function'] == self.current_function:
                    # Check for various protection mechanisms
                    if any(pattern in expr_text_lower for pattern in self.FRONT_RUNNING_PROTECTION_PATTERNS):
                        func_info['has_slippage_protection'] = True
                        
                    if 'deadline' in expr_text_lower or 'block.timestamp' in expr_text_lower:
                        func_info['has_deadline_check'] = True
                        
                    if any(pattern in expr_text_lower for pattern in self.COMMIT_REVEAL_PATTERNS):
                        func_info['has_commit_reveal'] = True
                        
                    # If function has any protection, mark as not vulnerable
                    if (func_info['has_commit_reveal'] or func_info['has_slippage_protection'] or 
                        func_info['has_deadline_check']):
                        func_info['vulnerable'] = False
                    break
                    
    def enterFunctionCall(self, ctx):
        """Check function calls for front-running protection patterns."""
        if not self.current_function or not self.current_contract:
            return
            
        call_text = ctx.getText()
        call_text_lower = call_text.lower()
        
        # Check for keccak256 calls (possible commitment scheme)
        if 'keccak256(' in call_text_lower:
            for func_info in self.trading_functions:
                if func_info['function'] == self.current_function:
                    func_info['has_commit_reveal'] = True
                    func_info['vulnerable'] = False
                    break
                    
    def enterEqualityComparison(self, ctx):
        """Check equality comparisons for commitment verification."""
        if not self.current_function or not self.current_contract:
            return
            
        comparison_text = ctx.getText()
        comparison_text_lower = comparison_text.lower()
        
        # Check for commitment verification comparisons
        if any(pattern in comparison_text_lower for pattern in self.COMMIT_REVEAL_PATTERNS):
            for func_info in self.trading_functions:
                if func_info['function'] == self.current_function:
                    func_info['has_commit_reveal'] = True
                    func_info['vulnerable'] = False
                    break
                    
    def get_violations(self):
        """Return list of detected violations."""
        return self.violations
