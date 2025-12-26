# S-ERC-003: Unindexed ERC20 Event Parameters
# Detects ERC20 events without indexed parameters
# Based on Slither's unindexed_event_parameters detector
# Impact: INFORMATIONAL | Confidence: HIGH

from antlr4 import *
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class UnindexedERC20EventDetector(SolidityParserListener):
    """
    Detects ERC20 events without indexed parameters.
    
    Issue: ERC20 Transfer and Approval events should have their first
    two parameters indexed for proper filtering and event querying.
    
    Expected:
    - event Transfer(address indexed from, address indexed to, uint256 value);
    - event Approval(address indexed owner, address indexed spender, uint256 value);
    
    Without indexed parameters, external tools may fail to properly
    index and search for these events.
    
    Recommendation: Add 'indexed' keyword to first two parameters.
    """
    
    def __init__(self):
        self.violations = []
    
    def enterEventDefinition(self, ctx):
        event_name = ctx.identifier(0).getText() if ctx.identifier(0) else "unknown"
        line = ctx.start.line
        
        if event_name not in ['Transfer', 'Approval']:
            return
        
        # Check if parameters are indexed
        event_text = ctx.getText()
        
        # Count indexed keywords
        indexed_count = event_text.count('indexed')
        
        if indexed_count < 2:
            missing = 2 - indexed_count
            self.violations.append(
                f"⚠️ [S-ERC-003] Unindexed ERC20 event parameters at line {line}: "
                f"Event '{event_name}' is missing {missing} indexed parameter(s). "
                f"First two parameters should be indexed for proper event filtering."
            )
    
    def get_violations(self):
        return self.violations
