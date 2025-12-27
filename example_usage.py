#!/usr/bin/env python3
"""
Example script demonstrating how to use ptsscan programmatically
"""

from ptsscan import SolidityScanner, Reporter
from pathlib import Path

def main():
    # Initialize scanner
    scanner = SolidityScanner(verbose=True)
    
    # Scan a single file
    print("Scanning single file...")
    results = scanner.scan_file("test_contracts/ReentrancyDetector_bad.sol")
    print(f"Found {len(results['bugs'])} issues")
    
    # Scan multiple files
    print("\nScanning multiple files...")
    all_results = []
    
    contracts_dir = Path("test_contracts")
    for sol_file in contracts_dir.glob("*.sol"):
        result = scanner.scan_file(str(sol_file))
        if result['bugs']:
            all_results.append(result)
    
    # Generate reports
    if all_results:
        reporter = Reporter(all_results)
        
        # Generate JSON report
        reporter.generate_json("example_results.json")
        print("\nJSON report saved to: example_results.json")
        
        # Generate Excel report
        reporter.generate_excel("example_results.xlsx")
        print("Excel report saved to: example_results.xlsx")
    else:
        print("\nNo issues found!")

if __name__ == "__main__":
    main()
