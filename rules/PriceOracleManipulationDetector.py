from antlr4 import *
from SolidityParserListener import SolidityParserListener

class PriceOracleManipulationDetector(SolidityParserListener):
    """
    Detector for SCWE-028: Price Oracle Manipulation
    Rule Code: 028
    
    Detects price oracle manipulation vulnerabilities including:
    - Direct use of oracle prices without validation
    - Missing price deviation checks
    - Absence of TWAP (Time-Weighted Average Price) mechanisms
    - Lack of circuit breakers for price manipulation
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.current_function = None
        self.processed_lines = set()
        self.function_has_price_protection = {}
        
        # Oracle price patterns
        self.oracle_patterns = [
            'oracle', 'price', 'priceOracle', 'priceFeed', 'getPrice',
            'latestPrice', 'currentPrice', 'priceData', 'priceSource'
        ]
        
        # Price protection patterns
        self.price_protection_patterns = [
            'twap', 'TWAP', 'timeWeighted', 'averagePrice', 'priceDeviation',
            'circuitBreaker', 'priceGuard', 'priceValidation', 'priceCheck',
            'maxDeviation', 'minPrice', 'maxPrice', 'priceRange'
        ]
        
        # Secure price validation patterns
        self.secure_patterns = [
            'require(price', 'assert(price', 'if (price',
            'require(deviation', 'assert(deviation', 'if (deviation',
            'require(twap', 'assert(twap', 'if (twap',
            'require(average', 'assert(average', 'if (average',
            'require(guard', 'assert(guard', 'if (guard',
            'require(validation', 'assert(validation', 'if (validation'
        ]
        
        # Functions that typically use oracle prices
        self.price_functions = [
            'deposit', 'withdraw', 'lend', 'borrow', 'swap', 'trade',
            'mint', 'burn', 'redeem', 'liquidate', 'settle'
        ]
    
    def enterContractDefinition(self, ctx):
        """Track contract definitions."""
        if ctx.identifier():
            self.current_contract = ctx.identifier().getText()
        else:
            self.current_contract = "UnknownContract"
    
    def exitContractDefinition(self, ctx):
        """Clear contract context when exiting."""
        self.current_contract = None
    
    def enterFunctionDefinition(self, ctx):
        """Track function definitions."""
        if not self.current_contract:
            return
            
        if ctx.identifier():
            self.current_function = ctx.identifier().getText()
        else:
            self.current_function = "unknown"
        
        # Initialize price protection tracking for this function
        if self.current_function:
            self.function_has_price_protection[self.current_function] = False
    
    def exitFunctionDefinition(self, ctx):
        """Analyze function for price protection when exiting."""
        if not self.current_contract or not self.current_function:
            return
        
        # Check if this function uses oracle prices and needs protection
        if self._is_price_function():
            # Check if the function has price protection
            if not self.function_has_price_protection.get(self.current_function, False):
                violation = {
                    'type': 'SCWE-028',
                    'contract': self.current_contract,
                    'function': self.current_function,
                    'line': ctx.start.line,
                    'message': f"Function '{self.current_function}' uses oracle prices without manipulation protection"
                }
                self.violations.append(violation)
        
        self.current_function = None
    
    def enterExpressionStatement(self, ctx):
        """Check for price protection patterns in function bodies."""
        if not self.current_function or not self.current_contract:
            return
            
        expr_text = ctx.getText()
        
        # Check for price protection patterns
        if any(pattern in expr_text for pattern in self.secure_patterns):
            self.function_has_price_protection[self.current_function] = True
    
    def enterVariableDeclarationStatement(self, ctx):
        """Check for price protection variables in function bodies."""
        if not self.current_function or not self.current_contract:
            return
            
        var_text = ctx.getText()
        
        # Check for price protection variable declarations
        if any(pattern in var_text for pattern in self.price_protection_patterns):
            self.function_has_price_protection[self.current_function] = True
    
    def _is_price_function(self):
        """Check if the current function is likely to use oracle prices."""
        if not self.current_function:
            return False
        
        func_lower = self.current_function.lower()
        return any(pattern.lower() in func_lower for pattern in self.price_functions)
    
    def get_violations(self):
        """Return all detected violations."""
        return self.violations
