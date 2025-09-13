import os
import importlib.util
from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser

RULES_DIR = "rules"

def load_all_rule_classes(rules_dir):
    rule_classes = []
    for filename in os.listdir(rules_dir):
        if filename.endswith(".py") and not filename.startswith("__"):
            filepath = os.path.join(rules_dir, filename)
            module_name = filename[:-3]  # Remove .py
            class_name = module_name  # Assuming class name = file name

            spec = importlib.util.spec_from_file_location(class_name, filepath)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            rule_class = getattr(mod, class_name)
            rule_instance = rule_class()
            rule_classes.append(rule_instance)
    return rule_classes

def parse_solidity_code(file_path):
    input_stream = FileStream(file_path)
    lexer = SolidityLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = SolidityParser(stream)
    tree = parser.sourceUnit()

    walker = ParseTreeWalker()
    rule_instances = load_all_rule_classes(RULES_DIR)
    
    for rule in rule_instances:
        walker.walk(rule, tree)
        if hasattr(rule, "get_violations"):
            for v in rule.get_violations():
                print(f"[{rule.__class__.__name__}] {v}")

# Run it
parse_solidity_code("test\InsecureUpgradeableProxy.sol")
