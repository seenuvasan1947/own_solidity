"""
PTSScan - Comprehensive Solidity Security Scanner
Main CLI entry point
"""

import argparse
import sys
import os
import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from colorama import init, Fore, Style
from tqdm import tqdm

from .scanner import SolidityScanner
from .reporter import Reporter

# Initialize colorama for cross-platform colored output
init(autoreset=True)

__version__ = "1.0.0"


def print_banner():
    """Print the PTSScan banner"""
    banner = f"""
{Fore.CYAN}╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   {Fore.YELLOW}██████╗ ████████╗███████╗███████╗ ██████╗ █████╗ ███╗   ██╗{Fore.CYAN}  ║
║   {Fore.YELLOW}██╔══██╗╚══██╔══╝██╔════╝██╔════╝██╔════╝██╔══██╗████╗  ██║{Fore.CYAN}  ║
║   {Fore.YELLOW}██████╔╝   ██║   ███████╗███████╗██║     ███████║██╔██╗ ██║{Fore.CYAN}  ║
║   {Fore.YELLOW}██╔═══╝    ██║   ╚════██║╚════██║██║     ██╔══██║██║╚██╗██║{Fore.CYAN}  ║
║   {Fore.YELLOW}██║        ██║   ███████║███████║╚██████╗██║  ██║██║ ╚████║{Fore.CYAN}  ║
║   {Fore.YELLOW}╚═╝        ╚═╝   ╚══════╝╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝{Fore.CYAN}  ║
║                                                           ║
║        {Fore.GREEN}Comprehensive Solidity Security Scanner v{__version__}{Fore.CYAN}       ║
║                  {Fore.MAGENTA}PTS Edition{Fore.CYAN}                                  ║
╚═══════════════════════════════════════════════════════════╝{Style.RESET_ALL}
    """
    print(banner)


def find_solidity_files(path: str, recursive: bool = True) -> List[str]:
    """
    Find all Solidity files in the given path
    
    Args:
        path: Directory or file path to scan
        recursive: Whether to scan subdirectories recursively
    
    Returns:
        List of absolute paths to .sol files
    """
    sol_files = []
    path_obj = Path(path)
    
    if path_obj.is_file():
        if path_obj.suffix == '.sol':
            sol_files.append(str(path_obj.absolute()))
    elif path_obj.is_dir():
        if recursive:
            # Recursively find all .sol files
            sol_files = [str(p.absolute()) for p in path_obj.rglob('*.sol')]
        else:
            # Only find .sol files in the current directory
            sol_files = [str(p.absolute()) for p in path_obj.glob('*.sol')]
    else:
        print(f"{Fore.RED}Error: Path '{path}' does not exist{Style.RESET_ALL}")
        sys.exit(1)
    
    return sorted(sol_files)


def create_arg_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser"""
    parser = argparse.ArgumentParser(
        prog='ptsscan',
        description='PTSScan - Comprehensive Solidity Security Scanner - Detect vulnerabilities in Solidity smart contracts',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan a single file
  ptsscan -i contract.sol
  
  # Scan a directory recursively
  ptsscan -i ./contracts -r
  
  # Scan and output to JSON
  ptsscan -i ./contracts -r -o results.json -f json
  
  # Scan and output to Excel
  ptsscan -i ./contracts -r -o results.xlsx -f excel
  
  # Scan with specific severity levels
  ptsscan -i ./contracts -r --severity high critical
  
  # Scan specific categories only
  ptsscan -i ./contracts -r --categories access_control reentrancy
  
  # Non-recursive scan
  ptsscan -i ./contracts -o results.json -f json
        """
    )
    
    # Required arguments
    parser.add_argument(
        '-i', '--input',
        required=True,
        help='Input file or directory path to scan'
    )
    
    # Optional arguments
    parser.add_argument(
        '-o', '--output',
        help='Output file path (default: ptsscan_results_<timestamp>.json)',
        default=None
    )
    
    parser.add_argument(
        '-f', '--format',
        choices=['json', 'excel', 'both'],
        default='json',
        help='Output format (default: json)'
    )
    
    parser.add_argument(
        '-r', '--recursive',
        action='store_true',
        help='Recursively scan subdirectories (default: False)'
    )
    
    parser.add_argument(
        '--severity',
        nargs='+',
        choices=['low', 'medium', 'high', 'critical'],
        help='Filter by severity levels (default: all)'
    )
    
    parser.add_argument(
        '--categories',
        nargs='+',
        help='Filter by specific categories (e.g., access_control, reentrancy)'
    )
    
    parser.add_argument(
        '--exclude',
        nargs='+',
        help='Exclude specific file patterns (e.g., *test*.sol, *mock*.sol)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )
    
    parser.add_argument(
        '--no-color',
        action='store_true',
        help='Disable colored output'
    )
    
    parser.add_argument(
        '--list-rules',
        action='store_true',
        help='List all available detection rules and exit'
    )
    
    return parser


def should_exclude_file(filepath: str, exclude_patterns: List[str]) -> bool:
    """Check if file should be excluded based on patterns"""
    if not exclude_patterns:
        return False
    
    from fnmatch import fnmatch
    filename = os.path.basename(filepath)
    
    for pattern in exclude_patterns:
        if fnmatch(filename, pattern):
            return True
    return False


def main():
    """Main CLI entry point"""
    parser = create_arg_parser()
    args = parser.parse_args()
    
    # Disable colors if requested
    if args.no_color:
        init(strip=True, convert=False)
    
    # Print banner
    print_banner()
    
    # Initialize scanner
    scanner = SolidityScanner(verbose=args.verbose)
    
    # List rules if requested
    if args.list_rules:
        scanner.list_rules()
        sys.exit(0)
    
    # Find all Solidity files
    print(f"{Fore.CYAN}[*] Scanning for Solidity files...{Style.RESET_ALL}")
    sol_files = find_solidity_files(args.input, args.recursive)
    
    # Apply exclusion patterns
    if args.exclude:
        original_count = len(sol_files)
        sol_files = [f for f in sol_files if not should_exclude_file(f, args.exclude)]
        excluded_count = original_count - len(sol_files)
        if excluded_count > 0:
            print(f"{Fore.YELLOW}[!] Excluded {excluded_count} file(s) based on patterns{Style.RESET_ALL}")
    
    if not sol_files:
        print(f"{Fore.RED}[!] No Solidity files found in '{args.input}'{Style.RESET_ALL}")
        sys.exit(1)
    
    print(f"{Fore.GREEN}[✓] Found {len(sol_files)} Solidity file(s){Style.RESET_ALL}\n")
    
    # Scan all files
    all_results = []
    total_bugs = 0
    
    print(f"{Fore.CYAN}[*] Starting security analysis...{Style.RESET_ALL}\n")
    
    for filepath in tqdm(sol_files, desc="Scanning files", unit="file"):
        if args.verbose:
            print(f"\n{Fore.CYAN}[*] Analyzing: {filepath}{Style.RESET_ALL}")
        
        try:
            results = scanner.scan_file(
                filepath,
                severity_filter=args.severity,
                category_filter=args.categories
            )
            
            if results['bugs']:
                total_bugs += len(results['bugs'])
                all_results.append(results)
                
                if args.verbose:
                    print(f"{Fore.YELLOW}  [!] Found {len(results['bugs'])} issue(s){Style.RESET_ALL}")
            elif args.verbose:
                print(f"{Fore.GREEN}  [✓] No issues found{Style.RESET_ALL}")
                
        except Exception as e:
            print(f"{Fore.RED}[!] Error scanning {filepath}: {str(e)}{Style.RESET_ALL}")
            if args.verbose:
                import traceback
                traceback.print_exc()
    
    # Generate summary
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Scan Summary{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"Files scanned: {Fore.YELLOW}{len(sol_files)}{Style.RESET_ALL}")
    print(f"Files with issues: {Fore.YELLOW}{len(all_results)}{Style.RESET_ALL}")
    print(f"Total issues found: {Fore.RED if total_bugs > 0 else Fore.GREEN}{total_bugs}{Style.RESET_ALL}")
    
    # Generate output
    if all_results:
        reporter = Reporter(all_results)
        
        # Determine output filename
        if args.output:
            output_base = args.output
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_base = f"ptsscan_results_{timestamp}"
        
        # Generate reports based on format
        if args.format in ['json', 'both']:
            json_file = output_base if output_base.endswith('.json') else f"{output_base}.json"
            reporter.generate_json(json_file)
            print(f"\n{Fore.GREEN}[✓] JSON report saved to: {json_file}{Style.RESET_ALL}")
        
        if args.format in ['excel', 'both']:
            excel_file = output_base if output_base.endswith('.xlsx') else f"{output_base}.xlsx"
            reporter.generate_excel(excel_file)
            print(f"{Fore.GREEN}[✓] Excel report saved to: {excel_file}{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.GREEN}[✓] No issues found! All contracts appear secure.{Style.RESET_ALL}")
    
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    # Exit with appropriate code
    sys.exit(0 if total_bugs == 0 else 1)


if __name__ == '__main__':
    main()
