from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class CommentsCoherenceDetector(SolidityParserListener):
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None
        self.function_start_line = None
        self.function_comments = []
        self.function_behavior = set()
        self.is_public_or_external = False

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"

    def exitContractDefinition(self, ctx):
        self.current_contract = None

    def enterFunctionDefinition(self, ctx):
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.function_start_line = ctx.start.line
        self.function_comments = []
        self.function_behavior = set()
        self.is_public_or_external = False
        
        # Check function visibility
        self._check_function_visibility(ctx)

    def _check_function_visibility(self, ctx):
        try:
            i = 0
            while True:
                vis = ctx.visibility(i)
                if vis is None:
                    break
                vis_text = vis.getText()
                if vis_text in ['public', 'external']:
                    self.is_public_or_external = True
                    break
                i += 1
        except Exception:
            pass

    def exitFunctionDefinition(self, ctx):
        if self.function_comments and self.function_behavior:
            self._check_comment_coherence()
        
        self.in_function = False
        self.function_name = None
        self.function_comments = []
        self.function_behavior = set()
        self.is_public_or_external = False

    def _check_comment_coherence(self):
        """Check if comments match the actual function behavior"""
        comment_text = " ".join(self.function_comments).lower()
        
        # Check for common comment-behavior mismatches
        mismatches = []
        
        # Check if comment mentions "safe" but function has risky operations
        if "safe" in comment_text and "risky_operations" in self.function_behavior:
            mismatches.append("Comment mentions 'safe' but function performs risky operations")
        
        # Check if comment mentions "view" but function modifies state
        if "view" in comment_text and "state_modification" in self.function_behavior:
            mismatches.append("Comment suggests read-only but function modifies state")
        
        # Check if comment mentions "owner only" but function is public
        if "owner" in comment_text and "only" in comment_text and self.is_public_or_external:
            mismatches.append("Comment suggests owner-only access but function is publicly accessible")
        
        # Check if comment mentions "validation" but no validation found
        if "validat" in comment_text and "validation" not in self.function_behavior:
            mismatches.append("Comment mentions validation but no validation logic found")
        
        if mismatches:
            mismatch_str = "; ".join(mismatches)
            self.violations.append(
                f"❌ [SOL-Basics-Function-4] Comment coherence issue in function '{self.function_name}' of contract '{self.current_contract}' at line {self.function_start_line}: {mismatch_str}"
            )

    def enterStatement(self, ctx):
        if not self.in_function:
            return
        self._analyze_statement(ctx.getText())

    def enterExpressionStatement(self, ctx):
        if not self.in_function:
            return
        self._analyze_statement(ctx.getText())

    def _analyze_statement(self, text):
        """Analyze statement to determine function behavior"""
        text_lower = text.lower()
        
        # State modifications
        if any(op in text for op in ["=", "+=", "-=", "*=", "/=", "%=", "++", "--", "delete"]):
            self.function_behavior.add("state_modification")
        
        # Risky operations
        if any(op in text_lower for op in ["transfer(", "send(", "call(", "delegatecall("]):
            self.function_behavior.add("risky_operations")
        
        # Validation logic
        if any(val in text_lower for val in ["require(", "assert(", "revert("]):
            self.function_behavior.add("validation")

    def visitTerminal(self, node):
        if self.in_function:
            # Collect comments - check for COMMENT and LINE_COMMENT token types
            if hasattr(node, 'symbol') and hasattr(node.symbol, 'type'):
                if node.symbol.type in [133, 134]:  # COMMENT, LINE_COMMENT
                    comment_text = node.getText()
                    self.function_comments.append(comment_text)

    def get_violations(self):
        return self.violations