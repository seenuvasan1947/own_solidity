# S-DEFI-002: Chainlink Feed Registry Usage
# Detects usage of Chainlink Feed Registry which is only available on Ethereum Mainnet
# Can cause deployment issues on other chains

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class ChainlinkFeedRegistryDetector(SolidityParserListener):
    """
    Detects usage of Chainlink Feed Registry.
    
    This detector identifies:
    1. Imports of FeedRegistryInterface
    2. Calls to Feed Registry functions
    3. Contracts using Feed Registry (Mainnet-only feature)
    
    False Positive Mitigation:
    - Only flags actual Feed Registry usage
    - Checks for specific Feed Registry functions
    - Provides informational warning (not critical)
    - Helps with multi-chain deployment awareness
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.uses_feed_registry = False
        self.feed_registry_calls = []  # List of (line, function_name)
        
        # Feed Registry specific functions
        self.registry_functions = [
            'decimals', 'description', 'version', 'latestRoundData',
            'getRoundData', 'latestAnswer', 'latestTimestamp', 'latestRound',
            'getAnswer', 'getTimestamp', 'getFeed', 'getPhaseFeed',
            'isFeedEnabled', 'getPhase', 'getRoundFeed', 'getPhaseRange',
            'getPreviousRoundId', 'getNextRoundId', 'proposeFeed',
            'confirmFeed', 'getProposedFeed', 'proposedGetRoundData',
            'proposedLatestRoundData', 'getCurrentPhaseId'
        ]

    def enterContractDefinition(self, ctx):
        """Track current contract"""
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.uses_feed_registry = False
        self.feed_registry_calls = []

    def enterImportDirective(self, ctx):
        """Check for Feed Registry imports"""
        text = ctx.getText()
        
        if 'FeedRegistryInterface' in text or 'FeedRegistry' in text:
            self.uses_feed_registry = True

    def enterStatement(self, ctx):
        """Check for Feed Registry function calls"""
        text = ctx.getText()
        line = ctx.start.line
        
        # Check if calling Feed Registry functions
        for func in self.registry_functions:
            if f'{func}(' in text or f'.{func}(' in text:
                # Check if it's on a registry object
                if 'registry.' in text.lower() or 'feedregistry' in text.lower():
                    self.feed_registry_calls.append((line, func))
                    self.uses_feed_registry = True

    def exitContractDefinition(self, ctx):
        """Check for violations when exiting contract"""
        if self.uses_feed_registry:
            message = f"ℹ️  [S-DEFI-002] INFO: Chainlink Feed Registry usage detected in contract '{self.current_contract}': " \
                     f"Feed Registry is only available on Ethereum Mainnet. "
            
            if self.feed_registry_calls:
                message += f"Found {len(self.feed_registry_calls)} Feed Registry call(s). "
            
            message += "If deploying to other chains (L2s, sidechains), use individual price feeds instead."
            
            self.violations.append(message)
        
        self.current_contract = None

    def get_violations(self):
        """Return all detected violations"""
        return self.violations
