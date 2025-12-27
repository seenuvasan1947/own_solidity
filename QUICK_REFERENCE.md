# SolScan Quick Reference

## Installation

```bash
# Install from source
cd own_solidity
pip install -r requirements.txt
pip install -e .

# Or use the installer
install.bat
```

## Basic Usage

```bash
# Scan single file
solscan -i contract.sol

# Scan directory recursively
solscan -i ./contracts -r

# Scan with output
solscan -i ./contracts -r -o results.json
```

## Common Commands

| Command | Description |
|---------|-------------|
| `solscan -i FILE` | Scan a single file |
| `solscan -i DIR -r` | Scan directory recursively |
| `solscan -i DIR -r -o results.json` | Save results to JSON |
| `solscan -i DIR -r -o results.xlsx -f excel` | Save results to Excel |
| `solscan -i DIR -r -f both` | Save both JSON and Excel |
| `solscan --list-rules` | List all detection rules |
| `solscan --help` | Show help message |
| `solscan --version` | Show version |

## Filtering

```bash
# By severity
solscan -i ./contracts -r --severity critical high

# By category
solscan -i ./contracts -r --categories access_control reentrancy

# Exclude files
solscan -i ./contracts -r --exclude "*test*.sol" "*mock*.sol"

# Verbose output
solscan -i ./contracts -r -v
```

## Output Formats

### JSON
```bash
solscan -i ./contracts -r -o results.json -f json
```

### Excel
```bash
solscan -i ./contracts -r -o results.xlsx -f excel
```

### Both
```bash
solscan -i ./contracts -r -o results -f both
```

## Severity Levels

- **Critical**: Immediate security risk
- **High**: Serious security issue
- **Medium**: Moderate concern
- **Low**: Minor issue

## Categories

- `access_control` - Authorization issues
- `reentrancy` - Reentrancy attacks
- `arithmetic` - Integer issues
- `gas_optimization` - Gas inefficiencies
- `code_quality` - Code quality issues
- `erc` - ERC standard compliance
- `assembly` - Low-level issues
- `compiler_bugs` - Compiler issues
- And more...

## Programmatic Usage

```python
from solscan import SolidityScanner, Reporter

# Scan a file
scanner = SolidityScanner()
results = scanner.scan_file("contract.sol")

# Generate reports
if results['bugs']:
    reporter = Reporter([results])
    reporter.generate_json("results.json")
    reporter.generate_excel("results.xlsx")
```

## Exit Codes

- `0` - No issues found
- `1` - Issues found or error occurred

## Tips

1. Use `-r` for recursive scanning
2. Use `--severity critical high` to focus on important issues
3. Use `-v` for detailed output during scanning
4. Use `--exclude` to skip test files
5. Use `-f both` to get both JSON and Excel reports

## Examples

### Scan entire project
```bash
solscan -i ./contracts -r -o security_report -f both
```

### Quick critical check
```bash
solscan -i ./contracts -r --severity critical
```

### Detailed scan with verbose output
```bash
solscan -i ./contracts -r -v -o detailed_results.json
```

### Scan excluding tests
```bash
solscan -i ./contracts -r --exclude "*test*.sol" "*Test.sol"
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Command not found | Run `pip install -e .` |
| Import errors | Run `pip install -r requirements.txt` |
| No rules loaded | Check `rules/` directory exists |
| Parser errors | Ensure valid Solidity syntax |

## Getting Help

```bash
solscan --help
```

For detailed documentation, see:
- `README.md` - Overview and features
- `INSTALLATION_GUIDE.md` - Detailed installation and usage
