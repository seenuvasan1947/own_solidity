# S-SEC-031: Unprotected Upgradeable Contract
# Detects upgradeable contracts without initialization protection
# Allows anyone to initialize and destroy the logic contract

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class UnprotectedUpgradeableDetector(SolidityParserListener):
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.is_upgradeable = False
        self.has_constructor_protection = False
        self.has_initializer = False
        self.has_selfdestruct = False
        self.has_delegatecall = False

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.is_upgradeable = False
        self.has_constructor_protection = False
        self.has_initializer = False
        self.has_selfdestruct = False
        self.has_delegatecall = False
        
        contract_text = ctx.getText()
        
        # Check if upgradeable (inherits from Initializable or similar)
        if 'Initializable' in contract_text or 'UUPSUpgradeable' in contract_text:
            self.is_upgradeable = True

    def exitContractDefinition(self, ctx):
        # Report if upgradeable without protection and has destructive functions
        if self.is_upgradeable and not self.has_constructor_protection:
            if self.has_initializer and (self.has_selfdestruct or self.has_delegatecall):
                self.violations.append(
                    f"❌ [S-SEC-031] HIGH: Unprotected upgradeable contract '{self.current_contract}': "
                    f"Contract has initializer function but no constructor protection. "
                    f"Anyone can initialize the logic contract and destroy it. "
                    f"Add constructor calling _disableInitializers() or use 'initializer' modifier protection."
                )
        
        self.current_contract = None

    def enterConstructorDefinition(self, ctx):
        if self.is_upgradeable:
            constructor_text = ctx.getText()
            # Check for _disableInitializers or initializer modifier
            if '_disableInitializers' in constructor_text or 'initializer' in constructor_text:
                self.has_constructor_protection = True

    def enterFunctionDefinition(self, ctx):
        func_text = ctx.getText()
        
        # Check for initializer functions
        if 'initializer' in func_text or 'reinitializer' in func_text:
            self.has_initializer = True
        
        # Check for selfdestruct
        if 'selfdestruct' in func_text or 'suicide' in func_text:
            self.has_selfdestruct = True
        
        # Check for delegatecall
        if 'delegatecall' in func_text:
            self.has_delegatecall = True

    def get_violations(self):
        return self.violations
