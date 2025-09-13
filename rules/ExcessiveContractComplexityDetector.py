from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class ExcessiveContractComplexityDetector(SolidityParserListener):
    """
    Rule Code: 002
    Detects excessive contract complexity as defined in SCWE-002
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.function_complexity = {}
        self.contract_functions = []
        self.contract_inheritance_depth = 0
        self.contract_functions_count = 0
        self.contract_lines_count = 0
        self.current_function = None
        self.function_nesting_depth = 0
        self.max_nesting_depth = 0
        self.function_conditions_count = 0
        self.function_loops_count = 0
        
    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.contract_functions_count = 0
        self.contract_lines_count = 0
        self.contract_inheritance_depth = 0
        
    def exitContractDefinition(self, ctx):
        # Check contract-level complexity metrics
        self._check_contract_complexity()
        self.current_contract = None
        
    def enterInheritanceSpecifierList(self, ctx):
        if self.current_contract:
            # Count inheritance depth
            inheritance_count = len(ctx.inheritanceSpecifier())
            self.contract_inheritance_depth = max(self.contract_inheritance_depth, inheritance_count)
    
    def enterFunctionDefinition(self, ctx):
        self.current_function = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.contract_functions_count += 1
        self.function_nesting_depth = 0
        self.max_nesting_depth = 0
        self.function_conditions_count = 0
        self.function_loops_count = 0
        
    def exitFunctionDefinition(self, ctx):
        if self.current_function:
            # Check function-level complexity
            self._check_function_complexity(ctx)
        self.current_function = None
        
    def enterIfStatement(self, ctx):
        if self.current_function:
            self.function_conditions_count += 1
            self.function_nesting_depth += 1
            self.max_nesting_depth = max(self.max_nesting_depth, self.function_nesting_depth)
    
    def exitIfStatement(self, ctx):
        if self.current_function:
            self.function_nesting_depth -= 1
    
    def enterForStatement(self, ctx):
        if self.current_function:
            self.function_loops_count += 1
            self.function_nesting_depth += 1
            self.max_nesting_depth = max(self.max_nesting_depth, self.function_nesting_depth)
    
    def exitForStatement(self, ctx):
        if self.current_function:
            self.function_nesting_depth -= 1
    
    def enterWhileStatement(self, ctx):
        if self.current_function:
            self.function_loops_count += 1
            self.function_nesting_depth += 1
            self.max_nesting_depth = max(self.max_nesting_depth, self.function_nesting_depth)
    
    def exitWhileStatement(self, ctx):
        if self.current_function:
            self.function_nesting_depth -= 1
    
    def enterDoWhileStatement(self, ctx):
        if self.current_function:
            self.function_loops_count += 1
            self.function_nesting_depth += 1
            self.max_nesting_depth = max(self.max_nesting_depth, self.function_nesting_depth)
    
    def exitDoWhileStatement(self, ctx):
        if self.current_function:
            self.function_nesting_depth -= 1
    
    def _check_contract_complexity(self):
        """Check for excessive contract complexity"""
        # Rule 1: Too many functions (more than 20)
        if self.contract_functions_count > 20:
            self.violations.append(
                f"❌ Excessive contract complexity in '{self.current_contract}': "
                f"Contract has {self.contract_functions_count} functions (threshold: 20). "
                f"Consider splitting into smaller contracts."
            )
        
        # Rule 2: Deep inheritance (more than 3 levels)
        if self.contract_inheritance_depth > 3:
            self.violations.append(
                f"❌ Excessive contract complexity in '{self.current_contract}': "
                f"Contract has inheritance depth of {self.contract_inheritance_depth} (threshold: 3). "
                f"Consider using composition over deep inheritance."
            )
    
    def _check_function_complexity(self, ctx):
        """Check for excessive function complexity"""
        if not self.current_function:
            return
            
        # Rule 1: Too many conditions (more than 10)
        if self.function_conditions_count > 10:
            self.violations.append(
                f"❌ Excessive function complexity in '{self.current_function}' of contract '{self.current_contract}': "
                f"Function has {self.function_conditions_count} conditions (threshold: 10). "
                f"Consider breaking down into smaller functions."
            )
        
        # Rule 2: Too many loops (more than 5)
        if self.function_loops_count > 5:
            self.violations.append(
                f"❌ Excessive function complexity in '{self.current_function}' of contract '{self.current_contract}': "
                f"Function has {self.function_loops_count} loops (threshold: 5). "
                f"Consider simplifying loop logic."
            )
        
        # Rule 3: Excessive nesting depth (more than 4 levels)
        if self.max_nesting_depth > 4:
            self.violations.append(
                f"❌ Excessive function complexity in '{self.current_function}' of contract '{self.current_contract}': "
                f"Function has nesting depth of {self.max_nesting_depth} (threshold: 4). "
                f"Consider refactoring to reduce nesting."
            )
        
        # Rule 4: Function is too long (more than 50 lines)
        function_lines = ctx.stop.line - ctx.start.line + 1
        if function_lines > 50:
            self.violations.append(
                f"❌ Excessive function complexity in '{self.current_function}' of contract '{self.current_contract}': "
                f"Function is {function_lines} lines long (threshold: 50). "
                f"Consider breaking into smaller functions."
            )
    
    def get_violations(self):
        return self.violations
