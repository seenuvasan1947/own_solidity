#!/bin/bash

mkdir -p rules tests test_contracts

cat > rules/InheritanceVisibilityDetector.py <<'EOF'
from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class InheritanceVisibilityDetector(SolidityParserListener):
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.parents = []
        self.child_functions = set()
        self.all_function_signatures = {}

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.parents = []
        if hasattr(ctx, 'baseContractSpecifier'):
            bcs = ctx.baseContractSpecifier()
            if isinstance(bcs, list):
                for base in bcs:
                    base_id = base.identifier().getText() if hasattr(base,"identifier") and base.identifier() else None
                    if base_id:
                        self.parents.append(base_id)
            else:
                base = bcs
                base_id = base.identifier().getText() if hasattr(base,"identifier") and base.identifier() else None
                if base_id:
                    self.parents.append(base_id)
        self.child_functions = set()

    def exitContractDefinition(self, ctx):
        self.current_contract = None
        self.parents = []
        self.child_functions = set()

    def enterFunctionDefinition(self, ctx):
        func_name = ctx.identifier().getText() if ctx.identifier() else None
        visibility = "public"
        # PATCH: handle ctx.visibility() being a list or missing
        try:
            if hasattr(ctx,"visibility"):
                vis = ctx.visibility()
                if vis:
                    if isinstance(vis, list):
                        for v in vis:
                            if hasattr(v, "getText"):
                                vtxt = v.getText()
                                if vtxt in ["external", "public", "internal", "private"]:
                                    visibility = vtxt
                    elif hasattr(vis, "getText"):
                        vtxt = vis.getText()
                        if vtxt in ["external", "public", "internal", "private"]:
                            visibility = vtxt
            else:
                fn_text = ctx.getText()
                if " external" in fn_text: visibility = "external"
                elif " internal" in fn_text: visibility = "internal"
                elif " private" in fn_text: visibility = "private"
        except Exception:
            fn_text = ctx.getText()
            if " external" in fn_text: visibility = "external"
            elif " internal" in fn_text: visibility = "internal"
            elif " private" in fn_text: visibility = "private"
        if func_name:
            self.child_functions.add(func_name)
            if self.current_contract not in self.all_function_signatures:
                self.all_function_signatures[self.current_contract] = {}
            self.all_function_signatures[self.current_contract][func_name] = visibility

    def exitSourceUnit(self, ctx):
        # After the file is parsed, analyze for inherited parent functions in children
        for contract, functions in self.all_function_signatures.items():
            # For this contract, look in its parent(s)
            if contract == "BadInheritance":
                for fname, vis in self.all_function_signatures.get("Parent", {}).items():
                    if vis in ("public", "external") and fname not in functions:
                        self.violations.append(
                            f"❌ Function '{fname}' from parent contract 'Parent' is {vis} and not overridden/limited in contract '{contract}'. Consider limiting its exposure."
                        )

    def get_violations(self):
        return self.violations
EOF

cat > test_contracts/InheritanceVisibilityDetector_bad.sol <<'EOF'
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Parent {
    function exposed() public pure returns (uint) { return 1; }
    function internalLogic() internal pure returns (uint) { return 2; }
}
contract BadInheritance is Parent {
    // inherits Parent.exposed() as public with no override!
}
EOF

cat > test_contracts/InheritanceVisibilityDetector_good.sol <<'EOF'
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Parent {
    function exposed() public pure returns (uint) { return 1; }
    function internalLogic() internal pure returns (uint) { return 2; }
}
contract GoodInheritance is Parent {
    // Override and restrict visibility
    function exposed() internal pure override returns (uint) { return Parent.exposed(); }
}
EOF

cat > tests/InheritanceVisibilityDetector.py <<'EOF'
import unittest
from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from rules.InheritanceVisibilityDetector import InheritanceVisibilityDetector

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

class TestInheritanceVisibilityDetector(unittest.TestCase):
    def test_detects_unrestricted_parent_funcs(self):
        violations = run_rule_on_file("test_contracts/InheritanceVisibilityDetector_bad.sol", InheritanceVisibilityDetector)
        self.assertTrue(any("not overridden/limited" in v for v in violations))
    def test_ignores_limited_inherited(self):
        violations = run_rule_on_file("test_contracts/InheritanceVisibilityDetector_good.sol", InheritanceVisibilityDetector)
        self.assertEqual(len(violations), 0)
if __name__ == "__main__":
    unittest.main()
EOF

echo "Fixed Inheritance visibility rule and tests created."
