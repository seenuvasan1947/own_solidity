# SolScan Installation & Usage Guide

## Installation

### Method 1: Install from Source (Development)

1. **Clone or navigate to the repository:**
   ```bash
   cd c:\Users\Finstein-Admin\Documents\cyber_product\own\own_solidity
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install the package in development mode:**
   ```bash
   pip install -e .
   ```

   This will install the package in "editable" mode, meaning you can modify the code and the changes will be reflected immediately.

### Method 2: Build and Install as Package

1. **Build the package:**
   ```bash
   python setup.py sdist bdist_wheel
   ```

2. **Install the built package:**
   ```bash
   pip install dist/solscan-1.0.0-py3-none-any.whl
   ```

### Method 3: Upload to PyPI (For Distribution)

1. **Install build tools:**
   ```bash
   pip install build twine
   ```

2. **Build the package:**
   ```bash
   python -m build
   ```

3. **Upload to PyPI:**
   ```bash
   # For test PyPI (recommended first)
   twine upload --repository testpypi dist/*
   
   # For production PyPI
   twine upload dist/*
   ```

4. **Install from PyPI:**
   ```bash
   pip install solscan
   ```

## Command-Line Usage

### Basic Commands

#### Scan a single file
```bash
solscan -i contract.sol
```

#### Scan a directory (non-recursive)
```bash
solscan -i ./contracts
```

#### Scan a directory recursively
```bash
solscan -i ./contracts -r
```

### Output Options

#### Generate JSON report (default)
```bash
solscan -i ./contracts -r -o results.json
```

#### Generate Excel report
```bash
solscan -i ./contracts -r -o results.xlsx -f excel
```

#### Generate both JSON and Excel
```bash
solscan -i ./contracts -r -o results -f both
```
This will create `results.json` and `results.xlsx`

#### Auto-generated filename with timestamp
```bash
solscan -i ./contracts -r
```
This will create `solscan_results_20251227_214000.json`

### Filtering Options

#### Filter by severity
```bash
# Only critical issues
solscan -i ./contracts -r --severity critical

# Critical and high severity
solscan -i ./contracts -r --severity critical high

# Medium and low severity
solscan -i ./contracts -r --severity medium low
```

#### Filter by category
```bash
# Only access control issues
solscan -i ./contracts -r --categories access_control

# Multiple categories
solscan -i ./contracts -r --categories access_control reentrancy arithmetic
```

#### Exclude files by pattern
```bash
# Exclude test files
solscan -i ./contracts -r --exclude "*test*.sol" "*mock*.sol"

# Exclude specific patterns
solscan -i ./contracts -r --exclude "*Test.sol" "*Mock.sol" "*Example.sol"
```

### Advanced Options

#### Verbose output
```bash
solscan -i ./contracts -r -v
```

#### Disable colored output
```bash
solscan -i ./contracts -r --no-color
```

#### List all available rules
```bash
solscan --list-rules
```

#### Check version
```bash
solscan --version
```

#### Get help
```bash
solscan --help
```

## Programmatic Usage

### Basic Example

```python
from solscan import SolidityScanner, Reporter

# Initialize scanner
scanner = SolidityScanner(verbose=True)

# Scan a file
results = scanner.scan_file("contract.sol")

# Check results
if results['bugs']:
    print(f"Found {len(results['bugs'])} issues")
    for bug in results['bugs']:
        print(f"- {bug['rule']}: {bug['violation']}")
```

### Scanning Multiple Files

```python
from pathlib import Path
from solscan import SolidityScanner, Reporter

scanner = SolidityScanner()
all_results = []

# Scan all .sol files in a directory
for sol_file in Path("contracts").rglob("*.sol"):
    result = scanner.scan_file(str(sol_file))
    if result['bugs']:
        all_results.append(result)

# Generate reports
if all_results:
    reporter = Reporter(all_results)
    reporter.generate_json("results.json")
    reporter.generate_excel("results.xlsx")
```

### With Filters

```python
scanner = SolidityScanner()

# Scan with severity filter
results = scanner.scan_file(
    "contract.sol",
    severity_filter=['critical', 'high']
)

# Scan with category filter
results = scanner.scan_file(
    "contract.sol",
    category_filter=['access_control', 'reentrancy']
)

# Scan with both filters
results = scanner.scan_file(
    "contract.sol",
    severity_filter=['critical', 'high'],
    category_filter=['access_control']
)
```

## Real-World Examples

### Example 1: CI/CD Integration

```bash
#!/bin/bash
# scan_contracts.sh

# Scan all contracts and fail if critical issues found
solscan -i ./contracts -r --severity critical -o scan_results.json

# Check exit code
if [ $? -ne 0 ]; then
    echo "Critical security issues found!"
    exit 1
fi

echo "No critical issues found"
exit 0
```

### Example 2: Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Get list of staged .sol files
STAGED_SOL=$(git diff --cached --name-only --diff-filter=ACM | grep '\.sol$')

if [ -n "$STAGED_SOL" ]; then
    echo "Scanning Solidity files..."
    
    for file in $STAGED_SOL; do
        solscan -i "$file" --severity critical high
        
        if [ $? -ne 0 ]; then
            echo "Security issues found in $file"
            echo "Please fix before committing"
            exit 1
        fi
    done
fi

exit 0
```

### Example 3: Automated Reporting

```python
#!/usr/bin/env python3
"""
Automated security scan with email reporting
"""

from solscan import SolidityScanner, Reporter
from pathlib import Path
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

def scan_and_report(contracts_dir, email_to):
    scanner = SolidityScanner()
    all_results = []
    
    # Scan all contracts
    for sol_file in Path(contracts_dir).rglob("*.sol"):
        result = scanner.scan_file(str(sol_file))
        if result['bugs']:
            all_results.append(result)
    
    if all_results:
        # Generate reports
        reporter = Reporter(all_results)
        reporter.generate_json("security_report.json")
        reporter.generate_excel("security_report.xlsx")
        
        # Send email with attachments
        send_email(
            to=email_to,
            subject="Security Scan Report",
            body=f"Found {sum(len(r['bugs']) for r in all_results)} issues",
            attachments=["security_report.json", "security_report.xlsx"]
        )

if __name__ == "__main__":
    scan_and_report("./contracts", "security@example.com")
```

## Understanding the Output

### JSON Report Structure

```json
{
  "scan_info": {
    "timestamp": "2025-12-27T21:40:00",
    "total_files": 10,
    "total_bugs": 25
  },
  "results": [
    {
      "file": "contracts/Token.sol",
      "bugs_count": 3,
      "rules_applied": 100,
      "bugs": [
        {
          "rule": "ReentrancyDetector",
          "category": "reentrancy",
          "severity": "critical",
          "description": "Potential reentrancy vulnerability",
          "violation": "❌ Reentrancy at line 45: transfer()"
        }
      ]
    }
  ],
  "summary": {
    "total_files": 10,
    "total_bugs": 25,
    "by_severity": {
      "critical": 5,
      "high": 10,
      "medium": 8,
      "low": 2
    },
    "by_category": {
      "reentrancy": 5,
      "access_control": 8,
      "arithmetic": 7,
      "code_quality": 5
    }
  }
}
```

### Excel Report Sheets

1. **Summary Sheet**: Overview with statistics
2. **All Issues Sheet**: Complete list of all findings
3. **By File Sheet**: Issues grouped by file
4. **By Category Sheet**: Issues grouped by category

## Troubleshooting

### Issue: Command not found

**Solution**: Make sure the package is installed correctly:
```bash
pip install -e .
```

### Issue: Import errors

**Solution**: Install all dependencies:
```bash
pip install -r requirements.txt
```

### Issue: No rules loaded

**Solution**: Make sure the `rules` directory is in the correct location and contains the detection rules.

### Issue: Parser errors

**Solution**: Ensure the Solidity files are syntactically correct. SolScan requires valid Solidity syntax.

## Best Practices

1. **Run regularly**: Integrate SolScan into your CI/CD pipeline
2. **Fix critical issues first**: Prioritize by severity
3. **Use filters**: Focus on specific categories during development
4. **Review reports**: Don't just rely on automated scans
5. **Keep updated**: Update SolScan regularly for new rules

## Support

For issues, questions, or feature requests:
- GitHub: https://github.com/yourusername/solscan
- Email: support@example.com
