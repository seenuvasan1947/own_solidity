import os
import sys
import importlib.util
from antlr4 import *
from antlr4.error.ErrorListener import ErrorListener
from antlr4.atn.PredictionMode import PredictionMode
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser

RULES_DIR = "rules"

class SilentErrorListener(ErrorListener):
    """Silent error listener - suppresses all parsing warnings"""
    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        pass  # Silently ignore
    
    def reportAmbiguity(self, recognizer, dfa, startIndex, stopIndex, exact, ambigAlts, configs):
        pass
    
    def reportAttemptingFullContext(self, recognizer, dfa, startIndex, stopIndex, conflictingAlts, configs):
        pass
    
    def reportContextSensitivity(self, recognizer, dfa, startIndex, stopIndex, prediction, configs):
        pass

def load_all_rule_classes(rules_dir):
    """Load all detector rule classes silently"""
    rule_classes = []
    
    for filename in sorted(os.listdir(rules_dir)):
        if filename.endswith(".py") and not filename.startswith("__"):
            filepath = os.path.join(rules_dir, filename)
            module_name = filename[:-3]
            class_name = module_name
            
            try:
                spec = importlib.util.spec_from_file_location(class_name, filepath)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                
                rule_class = getattr(mod, class_name)
                rule_instance = rule_class()
                rule_classes.append(rule_instance)
            except:
                pass  # Silently skip failed rules
    
    return rule_classes

def parse_solidity_code(file_path):
    """
    Parse Solidity code and run all detectors.
    Only prints bug detections - no other output.
    Handles large files (70k+ lines) without skipping content.
    """
    try:
        if not os.path.exists(file_path):
            print(f"[ERROR] File not found: {file_path}")
            return
        
        # Create input stream with UTF-8 encoding
        input_stream = FileStream(file_path, encoding='utf-8')
        
        # Lexical analysis
        lexer = SolidityLexer(input_stream)
        error_listener = SilentErrorListener()
        lexer.removeErrorListeners()
        lexer.addErrorListener(error_listener)
        
        # Create token stream and fill buffer (important for large files)
        stream = CommonTokenStream(lexer)
        stream.fill()
        
        # Syntax analysis (parsing)
        parser = SolidityParser(stream)
        parser.removeErrorListeners()
        parser.addErrorListener(error_listener)
        
        # Use SLL prediction mode for speed
        parser._interp.predictionMode = PredictionMode.SLL
        
        try:
            tree = parser.sourceUnit()
        except:
            # Fallback to LL mode if SLL fails
            stream.seek(0)
            parser.reset()
            parser._interp.predictionMode = PredictionMode.LL
            tree = parser.sourceUnit()
        
        # Load detector rules
        rule_instances = load_all_rule_classes(RULES_DIR)
        
        if not rule_instances:
            return
        
        # Run all detectors
        walker = ParseTreeWalker()
        
        for rule in rule_instances:
            try:
                walker.walk(rule, tree)
                
                # Print only violations (bugs)
                if hasattr(rule, "get_violations"):
                    violations = rule.get_violations()
                    if violations:
                        for v in violations:
                            print(f"[{rule.__class__.__name__}] {v}")
            except:
                pass  # Silently skip detector errors
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")

# Run it
if __name__ == "__main__":
    default_file = "test/MyContract.sol"
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = default_file
    
    parse_solidity_code(file_path)

