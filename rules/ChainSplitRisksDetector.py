from SolidityParserListener import SolidityParserListener

class ChainSplitRisksDetector(SolidityParserListener):
    """
    Rule Code: 001
    Detects SCWE-033: Chain Split Risks vulnerabilities
    
    Chain split risks refer to vulnerabilities that arise when a blockchain splits into multiple chains,
    such as during a hard fork. This can lead to confusion or inconsistencies in contract logic,
    loss of funds or data, and exploitation of vulnerabilities in cross-chain operations.
    """
    
    # Constants for chain ID keywords
    BLOCK_CHAINID = 'block.chainid'
    CHAINID_KEYWORDS = ['chainid', 'chain_id', 'networkid', 'network_id']
    CROSS_CHAIN_PATTERNS = [
        'processtransaction', 'bridgetransfer', 'crosschain', 'relay',
        'transfer', 'send', 'call', 'delegatecall', 'staticcall'
    ]
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.current_function = None
        self.has_chain_id_check = False
        self.has_chain_id_variable = False
        self.cross_chain_functions = []
        
    def enterContractDefinition(self, ctx):
        """Track contract definitions and reset chain ID tracking."""
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "UnknownContract"
        self.has_chain_id_check = False
        self.has_chain_id_variable = False
        self.cross_chain_functions = []
        
    def exitContractDefinition(self, ctx):
        """Check for missing chain split protection at contract level."""
        if self.current_contract and self.cross_chain_functions and not self.has_chain_id_variable:
            self.violations.append(
                f"SCWE-033: Contract '{self.current_contract}' appears to handle cross-chain operations "
                f"but lacks chain ID validation mechanism. Consider adding chain identifier checks."
            )
        self.current_contract = None
        
    def enterFunctionDefinition(self, ctx):
        """Track function definitions."""
        if not self.current_contract:
            return
            
        func_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.current_function = func_name
        
    def exitFunctionDefinition(self, ctx):
        """Reset function tracking."""
        self.current_function = None
        
    def enterStateVariableDeclaration(self, ctx):
        """Check for chain ID related state variables."""
        if not self.current_contract:
            return
            
        var_name = ctx.identifier().getText() if ctx.identifier() else ""
        var_name_lower = var_name.lower()
        
        # Check for chain ID related variables
        if any(keyword in var_name_lower for keyword in self.CHAINID_KEYWORDS):
            self.has_chain_id_variable = True
            
    def enterConstructorDefinition(self, ctx):
        """Check constructor for chain ID initialization."""
        if not self.current_contract:
            return
            
        constructor_text = ctx.getText()
        
        # Check if constructor initializes chain ID
        constructor_text_lower = constructor_text.lower()
        if any(keyword in constructor_text_lower for keyword in self.CHAINID_KEYWORDS) or self.BLOCK_CHAINID in constructor_text_lower:
            self.has_chain_id_variable = True
            
    def enterFunctionCall(self, ctx):
        """Check for cross-chain function calls and chain ID usage."""
        if not self.current_function or not self.current_contract:
            return
            
        call_text = ctx.getText()
        call_text_lower = call_text.lower()
        
        # Check for cross-chain related function calls
        if any(pattern in call_text_lower for pattern in self.CROSS_CHAIN_PATTERNS):
            self.cross_chain_functions.append({
                'function': self.current_function,
                'line': ctx.start.line,
                'call': call_text
            })
            
            # Check if this call includes chain ID validation
            if not (any(keyword in call_text_lower for keyword in self.CHAINID_KEYWORDS) or self.BLOCK_CHAINID in call_text_lower):
                self.violations.append(
                    f"SCWE-033: Function '{self.current_function}' at line {ctx.start.line} "
                    f"performs cross-chain operation without chain ID validation. "
                    f"Consider adding chain identifier checks to prevent chain split vulnerabilities."
                )
                
    def enterPrimaryExpression(self, ctx):
        """Check for block.chainid usage."""
        if not self.current_function or not self.current_contract:
            return
            
        expr_text = ctx.getText()
        
        # Check for block.chainid usage
        if self.BLOCK_CHAINID in expr_text.lower():
            self.has_chain_id_check = True
            
    def enterRequireStatement(self, ctx):
        """Check require statements for chain ID validation."""
        if not self.current_function or not self.current_contract:
            return
            
        require_text = ctx.getText()
        require_text_lower = require_text.lower()
        
        # Check if require statement validates chain ID
        if any(keyword in require_text_lower for keyword in self.CHAINID_KEYWORDS) or self.BLOCK_CHAINID in require_text_lower:
            self.has_chain_id_check = True
            
    def enterExpressionStatement(self, ctx):
        """Check expression statements for require calls with chain ID validation."""
        if not self.current_function or not self.current_contract:
            return
            
        expr_text = ctx.getText()
        expr_text_lower = expr_text.lower()
        
        # Check for require statements with chain ID validation
        if 'require(' in expr_text_lower and (any(keyword in expr_text_lower for keyword in self.CHAINID_KEYWORDS) or self.BLOCK_CHAINID in expr_text_lower):
            self.has_chain_id_check = True
            
    def enterIfStatement(self, ctx):
        """Check if statements for chain ID validation."""
        if not self.current_function or not self.current_contract:
            return
            
        if_text = ctx.getText()
        if_text_lower = if_text.lower()
        
        # Check if condition validates chain ID
        if any(keyword in if_text_lower for keyword in self.CHAINID_KEYWORDS) or self.BLOCK_CHAINID in if_text_lower:
            self.has_chain_id_check = True
            
    def enterEqualityComparison(self, ctx):
        """Check equality comparisons for chain ID validation."""
        if not self.current_function or not self.current_contract:
            return
            
        comparison_text = ctx.getText()
        comparison_text_lower = comparison_text.lower()
        
        # Check if comparison involves chain ID
        if any(keyword in comparison_text_lower for keyword in self.CHAINID_KEYWORDS) or self.BLOCK_CHAINID in comparison_text_lower:
            self.has_chain_id_check = True
            
    def enterParameterDeclaration(self, ctx):
        """Check function parameters for chain ID parameters."""
        if not self.current_function or not self.current_contract:
            return
            
        param_name = ctx.identifier().getText() if ctx.identifier() else ""
        param_name_lower = param_name.lower()
        
        # Check for chain ID related parameters
        if any(keyword in param_name_lower for keyword in self.CHAINID_KEYWORDS):
            # This suggests the function expects chain ID as parameter
            # Check if it's being validated
            pass  # Will be caught by other checks if validation is missing
            
    def get_violations(self):
        """Return list of detected violations."""
        return self.violations
