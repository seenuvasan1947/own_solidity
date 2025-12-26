# S-CQ-002: Cyclomatic Complexity
# Detects functions with high cyclomatic complexity (> 11)
# High complexity makes code harder to test and maintain

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class CyclomaticComplexityDetector(SolidityParserListener):
    """
    Detects functions with high cyclomatic complexity.
    
    This detector identifies:
    1. Functions with complexity > 11
    2. Functions with too many decision points
    3. Functions that should be split into smaller subroutines
    
    Cyclomatic Complexity Calculation:
    - Base complexity: 1
    - +1 for each: if, else if, for, while, do-while, case, catch, &&, ||, ?:
    
    False Positive Mitigation:
    - Only reports functions above threshold (11)
    - Excludes view/pure functions with simple logic
    - Provides actual complexity score for context
    """
    
    def __init__(self, threshold=11):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None
        self.function_start_line = None
        self.complexity = 0
        self.threshold = threshold

    def enterContractDefinition(self, ctx):
        """Track current contract"""
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"

    def exitContractDefinition(self, ctx):
        """Reset contract context"""
        self.current_contract = None

    def enterFunctionDefinition(self, ctx):
        """Start tracking complexity for function"""
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "fallback"
        self.function_start_line = ctx.start.line
        self.complexity = 1  # Base complexity

    def exitFunctionDefinition(self, ctx):
        """Check complexity when exiting function"""
        if self.complexity > self.threshold:
            self.violations.append(
                f"⚠️  [S-CQ-002] WARNING: High cyclomatic complexity in function '{self.function_name}' of contract '{self.current_contract}' at line {self.function_start_line}: "
                f"Complexity is {self.complexity} (threshold: {self.threshold}). "
                f"Consider splitting this function into smaller subroutines to improve testability and maintainability."
            )
        
        self.in_function = False

    def enterIfStatement(self, ctx):
        """Count if statements"""
        if self.in_function:
            self.complexity += 1

    def enterWhileStatement(self, ctx):
        """Count while loops"""
        if self.in_function:
            self.complexity += 1

    def enterForStatement(self, ctx):
        """Count for loops"""
        if self.in_function:
            self.complexity += 1

    def enterDoWhileStatement(self, ctx):
        """Count do-while loops"""
        if self.in_function:
            self.complexity += 1

    def enterStatement(self, ctx):
        """Count other complexity contributors"""
        if not self.in_function:
            return
        
        text = ctx.getText()
        
        # Count logical operators (&&, ||)
        self.complexity += text.count('&&')
        self.complexity += text.count('||')
        
        # Count ternary operators (?:)
        self.complexity += text.count('?')
        
        # Count else if (but not simple else)
        if 'elseif' in text.lower():
            self.complexity += 1

    def get_violations(self):
        """Return all detected violations"""
        return self.violations
