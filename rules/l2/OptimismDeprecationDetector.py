# S-L2-001: Optimism Deprecated Predeploy
# Detects usage of deprecated Optimism predeploy contracts and functions
# These will revert on Optimism

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class OptimismDeprecationDetector(SolidityParserListener):
    """
    Detects deprecated Optimism predeploys and functions.
    
    Deprecated predeploys:
    - 0x4200000000000000000000000000000000000000 (LegacyMessagePasser)
    - 0x4200000000000000000000000000000000000001 (L1MessageSender)
    - 0x4200000000000000000000000000000000000002 (DeployerWhitelist)
    - 0x4200000000000000000000000000000000000013 (L1BlockNumber)
    
    Deprecated GasPriceOracle functions (0x420...0F):
    - overhead(), scalar(), getL1GasUsed()
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        
        self.deprecated_addresses = [
            '0x4200000000000000000000000000000000000000',
            '0x4200000000000000000000000000000000000001',
            '0x4200000000000000000000000000000000000002',
            '0x4200000000000000000000000000000000000013',
        ]
        
        self.gas_oracle_address = '0x420000000000000000000000000000000000000F'
        self.deprecated_gas_functions = ['overhead', 'scalar', 'getL1GasUsed']

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"

    def exitContractDefinition(self, ctx):
        self.current_contract = None

    def enterStatement(self, ctx):
        text = ctx.getText()
        line = ctx.start.line
        
        # Check for deprecated addresses
        for addr in self.deprecated_addresses:
            if addr in text or addr.lower() in text.lower():
                self.violations.append(
                    f"⚠️  [S-L2-001] WARNING: Deprecated Optimism predeploy used in contract '{self.current_contract}' at line {line}: "
                    f"Address {addr} is deprecated and will cause reverts on Optimism."
                )
        
        # Check for deprecated GasPriceOracle functions
        if self.gas_oracle_address in text or self.gas_oracle_address.lower() in text.lower():
            for func in self.deprecated_gas_functions:
                if f'{func}(' in text or f'.{func}(' in text:
                    self.violations.append(
                        f"⚠️  [S-L2-001] WARNING: Deprecated Optimism GasPriceOracle function in contract '{self.current_contract}' at line {line}: "
                        f"Function '{func}()' is deprecated and will revert. Use updated Optimism predeploys."
                    )

    def get_violations(self):
        return self.violations
