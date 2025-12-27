#!/usr/bin/env python3
"""
Test script to verify ptsscan installation and functionality
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    try:
        from ptsscan import SolidityScanner, Reporter
        from antlr4 import FileStream, CommonTokenStream, ParseTreeWalker
        from SolidityLexer import SolidityLexer
        from SolidityParser import SolidityParser
        import openpyxl
        import colorama
        import tqdm
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

def test_scanner_initialization():
    """Test if scanner can be initialized"""
    print("\nTesting scanner initialization...")
    try:
        from ptsscan import SolidityScanner
        scanner = SolidityScanner(verbose=False)
        print(f"✓ Scanner initialized with {len(scanner.rules)} rules")
        return True
    except Exception as e:
        print(f"✗ Scanner initialization failed: {e}")
        return False

def test_file_scan():
    """Test scanning a sample file"""
    print("\nTesting file scan...")
    try:
        from ptsscan import SolidityScanner
        
        # Find a test contract
        test_contracts = Path("test_contracts")
        if not test_contracts.exists():
            print("⚠ test_contracts directory not found, skipping file scan test")
            return True
        
        sol_files = list(test_contracts.glob("*.sol"))
        if not sol_files:
            print("⚠ No .sol files found in test_contracts, skipping file scan test")
            return True
        
        scanner = SolidityScanner(verbose=False)
        test_file = str(sol_files[0])
        results = scanner.scan_file(test_file)
        
        print(f"✓ Successfully scanned {Path(test_file).name}")
        print(f"  - Rules applied: {results.get('rules_applied', 0)}")
        print(f"  - Issues found: {len(results.get('bugs', []))}")
        return True
    except Exception as e:
        print(f"✗ File scan failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_report_generation():
    """Test report generation"""
    print("\nTesting report generation...")
    try:
        from ptsscan import Reporter
        
        # Create dummy results
        dummy_results = [{
            'file': 'test.sol',
            'bugs': [{
                'rule': 'TestRule',
                'category': 'test',
                'severity': 'medium',
                'description': 'Test description',
                'violation': 'Test violation',
                'file': 'test.sol'
            }],
            'rules_applied': 1
        }]
        
        reporter = Reporter(dummy_results)
        
        # Test JSON generation
        json_file = "test_report.json"
        reporter.generate_json(json_file)
        if os.path.exists(json_file):
            print(f"✓ JSON report generated: {json_file}")
            os.remove(json_file)
        else:
            print("✗ JSON report not created")
            return False
        
        # Test Excel generation
        excel_file = "test_report.xlsx"
        reporter.generate_excel(excel_file)
        if os.path.exists(excel_file):
            print(f"✓ Excel report generated: {excel_file}")
            os.remove(excel_file)
        else:
            print("✗ Excel report not created")
            return False
        
        return True
    except Exception as e:
        print(f"✗ Report generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cli_available():
    """Test if CLI command is available"""
    print("\nTesting CLI availability...")
    try:
        import subprocess
        result = subprocess.run(
            ["ptsscan", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"✓ CLI command available: {result.stdout.strip()}")
            return True
        else:
            print("✗ CLI command failed")
            return False
    except FileNotFoundError:
        print("✗ CLI command not found in PATH")
        print("  Try: pip install -e .")
        return False
    except Exception as e:
        print(f"✗ CLI test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("="*60)
    print("ptsscan Installation Verification")
    print("="*60)
    
    tests = [
        test_imports,
        test_scanner_initialization,
        test_file_scan,
        test_report_generation,
        test_cli_available
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All tests passed! ptsscan is ready to use.")
        print("\nTry running:")
        print("  ptsscan --help")
        print("  ptsscan --list-rules")
        return 0
    else:
        print("\n✗ Some tests failed. Please check the errors above.")
        print("\nTroubleshooting:")
        print("  1. Make sure all dependencies are installed: pip install -r requirements.txt")
        print("  2. Install the package: pip install -e .")
        print("  3. Check that you're in the correct directory")
        return 1

if __name__ == "__main__":
    sys.exit(main())
