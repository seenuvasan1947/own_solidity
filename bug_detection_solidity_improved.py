import os
import sys
import importlib.util
from antlr4 import *
from antlr4.error.ErrorListener import ErrorListener
from antlr4.atn.PredictionMode import PredictionMode
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
import traceback

RULES_DIR = "rules"

class CustomErrorListener(ErrorListener):
    """Custom error listener to handle parsing errors gracefully"""
    def __init__(self):
        super(CustomErrorListener, self).__init__()
        self.errors = []
    
    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        error_msg = f"Syntax error at line {line}:{column} - {msg}"
        self.errors.append(error_msg)
        print(f"[PARSER WARNING] {error_msg}")
    
    def reportAmbiguity(self, recognizer, dfa, startIndex, stopIndex, exact, ambigAlts, configs):
        # Suppress ambiguity warnings for large files
        pass
    
    def reportAttemptingFullContext(self, recognizer, dfa, startIndex, stopIndex, conflictingAlts, configs):
        # Suppress full context warnings for large files
        pass
    
    def reportContextSensitivity(self, recognizer, dfa, startIndex, stopIndex, prediction, configs):
        # Suppress context sensitivity warnings for large files
        pass

def load_all_rule_classes(rules_dir):
    """Load all detector rule classes from the rules directory"""
    rule_classes = []
    failed_rules = []
    
    for filename in sorted(os.listdir(rules_dir)):
        if filename.endswith(".py") and not filename.startswith("__"):
            filepath = os.path.join(rules_dir, filename)
            module_name = filename[:-3]  # Remove .py
            class_name = module_name  # Assuming class name = file name
            
            try:
                spec = importlib.util.spec_from_file_location(class_name, filepath)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                
                rule_class = getattr(mod, class_name)
                rule_instance = rule_class()
                rule_classes.append(rule_instance)
                print(f"[INFO] Loaded detector: {class_name}")
            except Exception as e:
                failed_rules.append((class_name, str(e)))
                print(f"[WARNING] Failed to load {class_name}: {e}")
    
    if failed_rules:
        print(f"\n[SUMMARY] Successfully loaded {len(rule_classes)} detectors, {len(failed_rules)} failed")
    else:
        print(f"\n[SUMMARY] Successfully loaded all {len(rule_classes)} detectors")
    
    return rule_classes

def parse_solidity_code(file_path, verbose=False):
    """
    Parse Solidity code and run all detectors.
    Optimized for large files (70k+ lines).
    
    Args:
        file_path: Path to the Solidity file
        verbose: Enable verbose output for debugging
    
    Returns:
        Dictionary with parsing results and violations
    """
    print(f"\n{'='*80}")
    print(f"Analyzing: {file_path}")
    print(f"{'='*80}\n")
    
    results = {
        'file': file_path,
        'success': False,
        'violations': [],
        'errors': [],
        'stats': {}
    }
    
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            error_msg = f"File not found: {file_path}"
            print(f"[ERROR] {error_msg}")
            results['errors'].append(error_msg)
            return results
        
        # Get file stats
        file_size = os.path.getsize(file_path)
        with open(file_path, 'r', encoding='utf-8') as f:
            line_count = sum(1 for _ in f)
        
        results['stats']['file_size_bytes'] = file_size
        results['stats']['line_count'] = line_count
        
        print(f"[INFO] File size: {file_size:,} bytes")
        print(f"[INFO] Line count: {line_count:,} lines")
        
        # Warn for very large files
        if line_count > 50000:
            print(f"[WARNING] Large file detected ({line_count:,} lines). Processing may take longer...")
        
        # Step 1: Create input stream with proper encoding
        print(f"[STEP 1/5] Reading file...")
        input_stream = FileStream(file_path, encoding='utf-8')
        
        # Step 2: Lexical analysis
        print(f"[STEP 2/5] Performing lexical analysis...")
        lexer = SolidityLexer(input_stream)
        
        # Add custom error listener to lexer
        error_listener = CustomErrorListener()
        lexer.removeErrorListeners()
        lexer.addErrorListener(error_listener)
        
        # Create token stream
        stream = CommonTokenStream(lexer)
        
        # Force token stream to fill buffer (important for large files)
        # This ensures all tokens are processed
        stream.fill()
        token_count = len(stream.tokens)
        results['stats']['token_count'] = token_count
        print(f"[INFO] Tokens generated: {token_count:,}")
        
        # Step 3: Syntax analysis (parsing)
        print(f"[STEP 3/5] Performing syntax analysis...")
        parser = SolidityParser(stream)
        
        # Add custom error listener to parser
        parser.removeErrorListeners()
        parser.addErrorListener(error_listener)
        
        # Configure parser for better performance with large files
        # Increase prediction mode for better handling of complex grammars
        parser._interp.predictionMode = PredictionMode.SLL  # Use SLL prediction mode for speed
        
        try:
            # Parse the source unit (entry point of Solidity grammar)
            tree = parser.sourceUnit()
        except Exception as parse_error:
            # If SLL fails, try with LL mode (slower but more accurate)
            print(f"[WARNING] SLL parsing failed, retrying with LL mode...")
            stream.seek(0)  # Reset stream
            parser.reset()
            parser._interp.predictionMode = PredictionMode.LL
            tree = parser.sourceUnit()
        
        # Check for parsing errors
        if error_listener.errors:
            results['errors'].extend(error_listener.errors)
            print(f"[WARNING] Parsing completed with {len(error_listener.errors)} errors")
            if verbose:
                for err in error_listener.errors:
                    print(f"  - {err}")
        else:
            print(f"[SUCCESS] Parsing completed successfully")
        
        # Step 4: Load all detector rules
        print(f"[STEP 4/5] Loading detector rules...")
        rule_instances = load_all_rule_classes(RULES_DIR)
        
        if not rule_instances:
            print(f"[ERROR] No detector rules loaded!")
            results['errors'].append("No detector rules loaded")
            return results
        
        # Step 5: Run all detectors using tree walker
        print(f"\n[STEP 5/5] Running detectors...")
        print(f"{'-'*80}")
        
        walker = ParseTreeWalker()
        total_violations = 0
        
        for rule in rule_instances:
            rule_name = rule.__class__.__name__
            try:
                # Walk the parse tree with this detector
                walker.walk(rule, tree)
                
                # Collect violations
                if hasattr(rule, "get_violations"):
                    violations = rule.get_violations()
                    if violations:
                        for v in violations:
                            violation_msg = f"[{rule_name}] {v}"
                            print(violation_msg)
                            results['violations'].append({
                                'detector': rule_name,
                                'message': v
                            })
                            total_violations += 1
                
            except Exception as e:
                error_msg = f"Error in detector {rule_name}: {str(e)}"
                print(f"[ERROR] {error_msg}")
                results['errors'].append(error_msg)
                if verbose:
                    traceback.print_exc()
        
        print(f"{'-'*80}")
        print(f"\n[SUMMARY] Analysis complete!")
        print(f"  - Total violations found: {total_violations}")
        print(f"  - Detectors run: {len(rule_instances)}")
        print(f"  - Parsing errors: {len(error_listener.errors)}")
        
        results['success'] = True
        results['stats']['total_violations'] = total_violations
        results['stats']['detectors_run'] = len(rule_instances)
        
    except Exception as e:
        error_msg = f"Fatal error during analysis: {str(e)}"
        print(f"\n[FATAL ERROR] {error_msg}")
        results['errors'].append(error_msg)
        if verbose:
            traceback.print_exc()
    
    return results

def main():
    """Main entry point"""
    # Default file to analyze
    default_file = "test/MyContract.sol"
    
    # Check command line arguments
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = default_file
    
    # Check for verbose flag
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    
    # Run analysis
    results = parse_solidity_code(file_path, verbose=verbose)
    
    # Exit with appropriate code
    if results['success']:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
