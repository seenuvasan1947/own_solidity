# PTSScan Enhanced Reporting - Line Numbers & Code Snippets 🎯

## What's New

PTSScan now automatically extracts **line numbers** and **code snippets** from all violations - without modifying any rules! This is done through smart helper functions in the reporter module.

## Features

### ✅ Automatic Line Number Extraction

The reporter automatically parses violation messages to extract line numbers using multiple patterns:
- `"line 123"`
- `"at line 45"`
- `"[Line 67]"`
- `"on line 89"`

### ✅ Code Snippet Generation

For each detected issue, PTSScan now shows:
- **2 lines before** the problematic line
- **The problematic line** (marked with `>>>`)
- **2 lines after** the problematic line

Example:
```
       1 | // Bad: No access control
       2 | contract BadContract {
>>>    3 |     function withdrawAll() public {
       4 |         // dangerous
       5 |     }
```

## Enhanced Output Formats

### JSON Output

Each bug now includes:
```json
{
  "rule": "AccessControlDetector",
  "category": "access_control",
  "severity": "medium",
  "description": "No description available",
  "violation": "❌ [Line 3] Function `withdrawAll` lacks access control",
  "line_number": 3,
  "code_snippet": "       1 | // Bad: No access control\n       2 | contract BadContract {\n>>>    3 |     function withdrawAll() public {\n       4 |         // dangerous\n       5 |     }"
}
```

### Excel Output

The "All Issues" sheet now has **9 columns**:

| # | File | **Line** | Category | Rule | Severity | Description | Violation Details | **Code Snippet** |
|---|------|----------|----------|------|----------|-------------|-------------------|------------------|
| 1 | contract.sol | **3** | Access Control | AccessControlDetector | MEDIUM | ... | ... | **Code with context** |

**Enhancements:**
- **Line column**: Shows exact line number in blue, bold font
- **Code Snippet column**: Monospace font (Courier New) with wrapped text
- **Wide column**: 60 characters wide for easy reading

## How It Works (Professional Style)

### 1. Helper Functions (No Rule Changes!)

```python
def _extract_line_number(self, violation: str) -> Optional[int]:
    """Extract line number from violation message using regex patterns"""
    patterns = [
        r'line\s+(\d+)',
        r'\[Line\s+(\d+)\]',
        r'at\s+line\s+(\d+)',
        r'on\s+line\s+(\d+)',
    ]
    # Returns line number or None

def _get_code_snippet(self, filepath: str, line_number: int, context_lines: int = 2):
    """Extract code snippet from source file with context"""
    # Reads the file
    # Extracts lines around the issue
    # Formats with line numbers and >>> marker
    # Returns formatted snippet
```

### 2. Automatic Enhancement

When the Reporter is initialized, it automatically:
1. Processes all results
2. Extracts line numbers from violation messages
3. Reads source files to get code snippets
4. Adds this data to each bug entry

```python
def _enhance_results(self):
    """Enhance results by adding line numbers and code snippets"""
    for file_result in self.results:
        for bug in file_result['bugs']:
            line_num = self._extract_line_number(bug['violation'])
            bug['line_number'] = line_num
            
            if line_num:
                snippet = self._get_code_snippet(filepath, line_num)
                bug['code_snippet'] = snippet
```

## Benefits

### ✅ Professional Output
- Matches industry-standard tools (SonarQube, ESLint, etc.)
- Clear, actionable information
- Easy to locate and fix issues

### ✅ No Rule Modifications
- All existing rules work as-is
- Helper functions handle everything
- Clean separation of concerns

### ✅ Better Developer Experience
- See exactly where the issue is
- Understand the context immediately
- No need to open the file to find the line

## Example Usage

```bash
# Scan and generate enhanced reports
ptsscan -i ./contracts -r -o results -f both

# JSON will include line_number and code_snippet
# Excel will have Line and Code Snippet columns
```

## Comparison: Before vs After

### Before
```json
{
  "violation": "❌ [Line 3] Function lacks access control"
}
```

### After
```json
{
  "violation": "❌ [Line 3] Function lacks access control",
  "line_number": 3,
  "code_snippet": "       1 | // Bad: No access control\n       2 | contract BadContract {\n>>>    3 |     function withdrawAll() public {\n       4 |         // dangerous\n       5 |     }"
}
```

## Technical Details

### Pattern Matching
- Uses Python regex for flexible line number extraction
- Supports multiple formats from different rules
- Case-insensitive matching

### File Reading
- UTF-8 encoding support
- Graceful error handling
- Returns `None` if file cannot be read

### Code Formatting
- Line numbers right-aligned (4 digits)
- `>>>` marker for the problematic line
- Clean, readable format

## Professional Architecture

This implementation follows professional software engineering principles:

1. **Separation of Concerns**: Rules detect issues, reporter formats output
2. **DRY (Don't Repeat Yourself)**: One implementation for all rules
3. **Extensibility**: Easy to add more patterns or change formatting
4. **Robustness**: Handles missing files, invalid line numbers gracefully
5. **Maintainability**: Helper functions are well-documented and testable

## Result

PTSScan now provides **professional-grade reporting** with:
- ✅ Exact line numbers
- ✅ Code snippets with context
- ✅ Clear visual markers
- ✅ Multiple output formats
- ✅ No changes to existing rules

All achieved through clean, professional helper functions! 🎉
