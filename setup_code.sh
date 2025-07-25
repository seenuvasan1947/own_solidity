#!/bin/bash

mkdir -p rules tests test_contracts

cat > rules/MissingFuncInheritanceDetector.py <<'EOF'
from antlr4 import * 
from SolidityLexer import SolidityLexer 
from SolidityParser import SolidityParser 
from SolidityParserListener import SolidityParserListener 

class MissingFuncInheritanceDetector(SolidityParserListener):
    def __init__(self):
        self.violations = []
        self.contract_parents = {}       # contract_name: [parent1, parent2]
        self.contract_funcs = {}         # contract_name: set(func1, func2)
        self.parent_required_funcs = {}  # parent_contract: [required_func1, required_func2]
        self.current_contract = None

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"
        # Get inheritance chain
        parents = []
        if hasattr(ctx, "baseContractSpecifier") and ctx.baseContractSpecifier():
            bases = ctx.baseContractSpecifier()
            if not isinstance(bases, list): bases = [bases]
            for base in bases:
                base_id = base.identifier().getText() if hasattr(base,"identifier") else None
                if base_id: parents.append(base_id)
        self.contract_parents[self.current_contract] = parents
        self.contract_funcs[self.current_contract] = set()

    def exitContractDefinition(self, ctx):
        self.current_contract = None

    def enterFunctionDefinition(self, ctx):
        func_name = ctx.identifier().getText() if ctx.identifier() else None
        if func_name and self.current_contract:
            self.contract_funcs[self.current_contract].add(func_name)

    def get_all_parents(self, contract, cache=None):
        if cache is None: cache = set()
        for parent in self.contract_parents.get(contract, []):
            if parent not in cache:
                cache.add(parent)
                self.get_all_parents(parent, cache)
        return cache

    # Example: Pausable parent expects 'pause' and 'unpause',
    # OwnerAdmin expects 'changeAdmin', etc.
    # Customize these as needed for your context.
    def get_required_parent_funcs(self, parent):
        if parent == "Pausable":
            return ["pause", "unpause"]
        elif parent == "OwnerAdmin":
            return ["changeAdmin"]
        else:
            # Add more parent->required-func mappings here
            return []

    def exitSourceUnit(self, ctx):
        for contract in self.contract_parents:
            all_parents = self.get_all_parents(contract)
            for parent in all_parents:
                required_funcs = self.get_required_parent_funcs(parent)
                for func in required_funcs:
                    if func not in self.contract_funcs[contract]:
                        self.violations.append(
                            f"❌ Contract '{contract}' inherits from '{parent}' but does not implement required function '{func}'"
                        )

    def get_violations(self):
        return self.violations
EOF

cat > test_contracts/MissingFuncInheritanceDetector_bad.sol <<'EOF'
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Pausable {
    function _requirePauseFuncs() internal virtual;
    bool public paused;
    // Intended for children to implement pause/unpause!
}
contract BadInherited is Pausable {
    // No implementation of pause/unpause!
}
EOF

cat > test_contracts/MissingFuncInheritanceDetector_good.sol <<'EOF'
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Pausable {
    bool public paused;
    // Intended for children to implement pause/unpause!
}
contract GoodInherited is Pausable {
    function pause() public { paused = true; }
    function unpause() public { paused = false; }
}
EOF

cat > tests/MissingFuncInheritanceDetector.py <<'EOF'
import unittest
from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from rules.MissingFuncInheritanceDetector import MissingFuncInheritanceDetector

def run_rule_on_file(filepath, rule_class):
    input_stream = FileStream(filepath)
    lexer = SolidityLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = SolidityParser(stream)
    tree = parser.sourceUnit()
    rule_instance = rule_class()
    walker = ParseTreeWalker()
    walker.walk(rule_instance, tree)
    return rule_instance.get_violations()

class TestMissingFuncInheritanceDetector(unittest.TestCase):
    def setUp(self):
        from rules.MissingFuncInheritanceDetector import MissingFuncInheritanceDetector
        self.rule = MissingFuncInheritanceDetector
        self.rule = MissingFuncInheritanceDetector

    def test_detects_not_implemented(self):
        violations = run_rule_on_file("test_contracts/MissingFuncInheritanceDetector_bad.sol", self.rule)
        self.assertTrue(any("does not implement required function" in v for v in violations))
    def test_approves_implemented(self):
        violations = run_rule_on_file("test_contracts/MissingFuncInheritanceDetector_good.sol", self.rule)
        self.assertEqual(len(violations), 0)
if __name__ == "__main__":
    unittest.main()
EOF

echo "MissingFuncInheritanceDetector rule, tests, and contract samples created."
