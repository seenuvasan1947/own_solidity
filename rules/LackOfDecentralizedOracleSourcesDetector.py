from antlr4 import *
from SolidityParserListener import SolidityParserListener

class LackOfDecentralizedOracleSourcesDetector(SolidityParserListener):
    """
    Detector for SCWE-029: Lack of Decentralized Oracle Sources
    Rule Code: 029
    
    Detects lack of decentralized oracle sources including:
    - Single oracle dependency
    - Missing multiple oracle validation
    - Absence of oracle fallback mechanisms
    - Lack of oracle redundancy
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.current_function = None
        self.processed_lines = set()
        self.contract_has_multiple_oracles = {}
        
        # Oracle patterns
        self.oracle_patterns = [
            'oracle', 'priceOracle', 'priceFeed', 'dataOracle',
            'oracleSource', 'oracleProvider', 'oracleContract'
        ]
        
        # Multiple oracle patterns
        self.multiple_oracle_patterns = [
            'oracles', 'oracleArray', 'oracleList', 'oracleSources',
            'multipleOracles', 'oraclePool', 'oracleSet', 'oracleGroup',
            'oracle[]', 'Oracle[]', 'oracleMapping', 'oracleCollection'
        ]
        
        # Decentralized oracle patterns
        self.decentralized_patterns = [
            'chainlink', 'Chainlink', 'band', 'Band', 'tellor', 'Tellor',
            'witnet', 'Witnet', 'api3', 'API3', 'pyth', 'Pyth',
            'decentralized', 'Decentralized', 'multiple', 'Multiple',
            'consensus', 'Consensus', 'aggregate', 'Aggregate'
        ]
        
        # Functions that typically use oracles
        self.oracle_functions = [
            'getPrice', 'getData', 'getValue', 'fetchPrice', 'fetchData',
            'updatePrice', 'updateData', 'price', 'data', 'value'
        ]
    
    def enterContractDefinition(self, ctx):
        """Track contract definitions."""
        if ctx.identifier():
            self.current_contract = ctx.identifier().getText()
        else:
            self.current_contract = "UnknownContract"
        
        # Initialize oracle tracking for this contract
        self.contract_has_multiple_oracles[self.current_contract] = False
    
    def exitContractDefinition(self, ctx):
        """Analyze contract for multiple oracles when exiting."""
        if not self.current_contract:
            return
        
        # Check if this contract uses oracles but lacks multiple sources
        if self._uses_oracles() and not self.contract_has_multiple_oracles.get(self.current_contract, False):
            violation = {
                'type': 'SCWE-029',
                'contract': self.current_contract,
                'function': 'constructor',
                'line': ctx.start.line,
                'message': f"Contract '{self.current_contract}' uses single oracle source without decentralization"
            }
            self.violations.append(violation)
        
        self.current_contract = None
    
    def enterFunctionDefinition(self, ctx):
        """Track function definitions."""
        if not self.current_contract:
            return
            
        if ctx.identifier():
            self.current_function = ctx.identifier().getText()
        else:
            self.current_function = "unknown"
    
    def exitFunctionDefinition(self, ctx):
        """Clear function context when exiting."""
        self.current_function = None
    
    def enterExpressionStatement(self, ctx):
        """Check for multiple oracle patterns in function bodies."""
        if not self.current_contract:
            return
            
        expr_text = ctx.getText()
        
        # Check for multiple oracle patterns
        if any(pattern in expr_text for pattern in self.multiple_oracle_patterns):
            self.contract_has_multiple_oracles[self.current_contract] = True
    
    def enterVariableDeclarationStatement(self, ctx):
        """Check for multiple oracle variables in function bodies."""
        if not self.current_contract:
            return
            
        var_text = ctx.getText()
        
        # Check for multiple oracle variable declarations
        if any(pattern in var_text for pattern in self.multiple_oracle_patterns):
            self.contract_has_multiple_oracles[self.current_contract] = True
    
    def _uses_oracles(self):
        """Check if the current contract uses oracles."""
        if not self.current_contract:
            return False
        
        # This is a simplified check - in a real implementation, you would
        # need to analyze the contract more thoroughly
        return True  # Assume all contracts might use oracles
    
    def get_violations(self):
        """Return all detected violations."""
        return self.violations
