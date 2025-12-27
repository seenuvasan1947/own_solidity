"""
PTSScan Scanner Module
Handles the actual scanning logic and rule execution
"""

import os
import sys
import importlib
import importlib.util
import inspect
from pathlib import Path
from typing import List, Dict, Any, Optional
from antlr4 import FileStream, CommonTokenStream, ParseTreeWalker
from colorama import Fore, Style

# Add parent directory to path to import parser
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener


class SolidityScanner:
    """Main scanner class that orchestrates rule execution"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.rules = self._load_rules()
        
        if self.verbose:
            print(f"{Fore.CYAN}[*] Loaded {len(self.rules)} detection rules{Style.RESET_ALL}")
    
    def _load_rules(self) -> List[Dict[str, Any]]:
        """
        Dynamically load all rule classes from the rules directory
        
        Returns:
            List of rule metadata dictionaries
        """
        rules = []
        rules_dir = current_dir / 'rules'
        
        if not rules_dir.exists():
            print(f"{Fore.RED}[!] Rules directory not found: {rules_dir}{Style.RESET_ALL}")
            return rules
        
        # Get all subdirectories (categories)
        categories = [d for d in rules_dir.iterdir() if d.is_dir() and not d.name.startswith('__')]
        
        for category_dir in categories:
            category_name = category_dir.name
            
            # Find all Python files in the category
            for rule_file in category_dir.glob('*.py'):
                if rule_file.name.startswith('__'):
                    continue
                
                try:
                    # Import the module
                    module_name = f"rules.{category_name}.{rule_file.stem}"
                    spec = importlib.util.spec_from_file_location(module_name, rule_file)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Find all classes that inherit from SolidityParserListener
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if issubclass(obj, SolidityParserListener) and obj != SolidityParserListener:
                            rules.append({
                                'name': name,
                                'class': obj,
                                'category': category_name,
                                'file': str(rule_file),
                                'severity': self._extract_severity(obj),
                                'description': self._extract_description(obj)
                            })
                            
                except Exception as e:
                    if self.verbose:
                        print(f"{Fore.YELLOW}[!] Failed to load rule from {rule_file}: {e}{Style.RESET_ALL}")
        
        return rules
    
    def _extract_severity(self, rule_class) -> str:
        """Extract severity from rule class docstring or attributes"""
        # Check for severity attribute
        if hasattr(rule_class, 'SEVERITY'):
            return rule_class.SEVERITY.lower()
        
        # Try to extract from docstring
        if rule_class.__doc__:
            doc = rule_class.__doc__.lower()
            if 'critical' in doc:
                return 'critical'
            elif 'high' in doc:
                return 'high'
            elif 'medium' in doc:
                return 'medium'
            elif 'low' in doc:
                return 'low'
        
        return 'medium'  # Default
    
    def _extract_description(self, rule_class) -> str:
        """Extract description from rule class"""
        if hasattr(rule_class, 'DESCRIPTION'):
            return rule_class.DESCRIPTION
        
        if rule_class.__doc__:
            # Get first line of docstring
            return rule_class.__doc__.strip().split('\n')[0]
        
        return "No description available"
    
    def scan_file(
        self,
        filepath: str,
        severity_filter: Optional[List[str]] = None,
        category_filter: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Scan a single Solidity file with all applicable rules
        
        Args:
            filepath: Path to the Solidity file
            severity_filter: List of severity levels to include
            category_filter: List of categories to include
        
        Returns:
            Dictionary containing scan results
        """
        results = {
            'file': filepath,
            'bugs': [],
            'scan_time': None,
            'rules_applied': 0
        }
        
        try:
            # Parse the Solidity file
            input_stream = FileStream(filepath, encoding='utf-8')
            lexer = SolidityLexer(input_stream)
            stream = CommonTokenStream(lexer)
            parser = SolidityParser(stream)
            tree = parser.sourceUnit()
            
            # Apply each rule
            for rule_info in self.rules:
                # Apply filters
                if severity_filter and rule_info['severity'] not in severity_filter:
                    continue
                
                if category_filter and rule_info['category'] not in category_filter:
                    continue
                
                try:
                    # Instantiate the rule
                    rule_instance = rule_info['class']()
                    
                    # Walk the parse tree
                    walker = ParseTreeWalker()
                    walker.walk(rule_instance, tree)
                    
                    # Get violations
                    if hasattr(rule_instance, 'get_violations'):
                        violations = rule_instance.get_violations()
                        
                        # Add violations to results
                        for violation in violations:
                            results['bugs'].append({
                                'rule': rule_info['name'],
                                'category': rule_info['category'],
                                'severity': rule_info['severity'],
                                'description': rule_info['description'],
                                'violation': violation,
                                'file': filepath
                            })
                    
                    results['rules_applied'] += 1
                    
                except Exception as e:
                    if self.verbose:
                        print(f"{Fore.YELLOW}[!] Error applying rule {rule_info['name']}: {e}{Style.RESET_ALL}")
            
        except Exception as e:
            if self.verbose:
                print(f"{Fore.RED}[!] Error parsing {filepath}: {e}{Style.RESET_ALL}")
            raise
        
        return results
    
    def list_rules(self):
        """Print all available rules organized by category"""
        print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Available Detection Rules{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
        
        # Group rules by category
        categories = {}
        for rule in self.rules:
            cat = rule['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(rule)
        
        # Print rules by category
        for category, rules in sorted(categories.items()):
            print(f"{Fore.YELLOW}Category: {category.upper().replace('_', ' ')}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'-'*80}{Style.RESET_ALL}")
            
            for rule in sorted(rules, key=lambda x: x['name']):
                severity_color = {
                    'critical': Fore.RED,
                    'high': Fore.LIGHTRED_EX,
                    'medium': Fore.YELLOW,
                    'low': Fore.LIGHTBLUE_EX
                }.get(rule['severity'], Fore.WHITE)
                
                print(f"  {Fore.GREEN}• {rule['name']}{Style.RESET_ALL}")
                print(f"    Severity: {severity_color}{rule['severity'].upper()}{Style.RESET_ALL}")
                print(f"    Description: {rule['description']}")
                print()
            
            print()
        
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}Total Rules: {len(self.rules)}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
