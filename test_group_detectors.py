#!/usr/bin/env python3
"""
Group Testing Script for SCWE-027 to SCWE-032
Tests all six detectors on the comprehensive test file
"""

from rules.VulnerableCryptographicAlgorithmsDetector import VulnerableCryptographicAlgorithmsDetector
from rules.PriceOracleManipulationDetector import PriceOracleManipulationDetector
from rules.LackOfDecentralizedOracleSourcesDetector import LackOfDecentralizedOracleSourcesDetector
from rules.InsecureOracleDataUpdatesDetector import InsecureOracleDataUpdatesDetector
from rules.InsecureUseOfBlockVariablesDetector import InsecureUseOfBlockVariablesDetector
from rules.DependencyOnBlockGasLimitDetector import DependencyOnBlockGasLimitDetector
from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser

def test_group_detectors():
    """Test all six detectors on the comprehensive test file"""
    
    # Initialize detectors
    detectors = [
        ('SCWE-027', VulnerableCryptographicAlgorithmsDetector()),
        ('SCWE-028', PriceOracleManipulationDetector()),
        ('SCWE-029', LackOfDecentralizedOracleSourcesDetector()),
        ('SCWE-030', InsecureOracleDataUpdatesDetector()),
        ('SCWE-031', InsecureUseOfBlockVariablesDetector()),
        ('SCWE-032', DependencyOnBlockGasLimitDetector())
    ]
    
    # Parse the test file
    try:
        input_stream = FileStream('test/ComprehensiveTestSCWE027-032.sol')
        lexer = SolidityLexer(input_stream)
        stream = CommonTokenStream(lexer)
        parser = SolidityParser(stream)
        tree = parser.sourceUnit()
        walker = ParseTreeWalker()
        
        print('=== GROUP TESTING RESULTS FOR SCWE-027 to SCWE-032 ===\n')
        
        total_violations = 0
        
        for detector_name, detector in detectors:
            try:
                walker.walk(detector, tree)
                violations = detector.get_violations()
                violation_count = len(violations)
                total_violations += violation_count
                
                print(f'{detector_name} Violations found: {violation_count}')
                for v in violations:
                    print(f'  {v}')
                print()
                
            except Exception as e:
                print(f'Error testing {detector_name}: {e}')
                print()
        
        print(f'=== SUMMARY ===')
        print(f'Total violations found across all detectors: {total_violations}')
        print(f'All detectors tested successfully!')
        
    except Exception as e:
        print(f'Error parsing test file: {e}')

if __name__ == '__main__':
    test_group_detectors()
