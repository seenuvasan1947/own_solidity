# S-FNC-001: Incorrect Modifier
# Detects modifiers that don't always execute _ or revert
# Can lead to functions returning default values unexpectedly

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class IncorrectModifierDetector(SolidityParserListener):
    """
    Detects modifiers that can return default values instead of executing function body.
    
    This detector identifies:
    1. Modifiers without _ (placeholder) in all code paths
    2. Modifiers without revert in all code paths
    3. Conditional modifiers that may skip function execution
    
    False Positive Mitigation:
    - Checks for _ (placeholder) in modifier body
    - Checks for revert/require/assert statements
    - Analyzes control flow paths
    - Excludes modifiers with proper guards
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_modifier = False
        self.modifier_name = None
        self.modifier_start_line = None
        self.has_placeholder = False
        self.has_revert = False
        self.has_conditional = False
        self.modifier_body = ""

    def enterContractDefinition(self, ctx):
        """Track current contract"""
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"

    def exitContractDefinition(self, ctx):
        """Reset contract context"""
        self.current_contract = None

    def enterModifierDefinition(self, ctx):
        """Analyze modifier for correctness"""
        self.in_modifier = True
        self.modifier_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.modifier_start_line = ctx.start.line
        self.has_placeholder = False
        self.has_revert = False
        self.has_conditional = False
        self.modifier_body = ctx.getText()

    def enterStatement(self, ctx):
        """Check statements in modifier"""
        if not self.in_modifier:
            return
        
        text = ctx.getText()
        text_lower = text.lower()
        
        # Check for placeholder _
        if '_' in text and ';' in text:
            # Make sure it's the placeholder, not just underscore in variable name
            if '_;' in text or '_ ;' in text:
                self.has_placeholder = True
        
        # Check for revert/require/assert
        if any(keyword in text_lower for keyword in ['revert(', 'require(', 'assert(']):
            self.has_revert = True
        
        # Check for conditionals
        if 'if(' in text_lower or 'if (' in text_lower:
            self.has_conditional = True

    def exitModifierDefinition(self, ctx):
        """Check for violations when exiting modifier"""
        # Check if modifier has placeholder in body
        if '_' in self.modifier_body:
            self.has_placeholder = True
        
        # If modifier has conditional but no guaranteed placeholder or revert
        if self.has_conditional:
            # Check if placeholder is inside conditional (risky)
            # Simplified check: if we have conditional and placeholder, it might be conditional
            if self.has_placeholder and not self._has_unconditional_placeholder():
                self.violations.append(
                    f"⚠️  [S-FNC-001] WARNING: Modifier '{self.modifier_name}' in contract '{self.current_contract}' at line {self.modifier_start_line}: "
                    f"Modifier contains conditional logic and may not always execute _ or revert. "
                    f"This can cause the function to return default values. Ensure all code paths execute _ or revert."
                )
        elif not self.has_placeholder and not self.has_revert:
            # No placeholder and no revert at all
            self.violations.append(
                f"❌ [S-FNC-001] CRITICAL: Modifier '{self.modifier_name}' in contract '{self.current_contract}' at line {self.modifier_start_line}: "
                f"Modifier does not execute _ (placeholder) or revert. Functions using this modifier will return default values."
            )
        
        self.in_modifier = False

    def _has_unconditional_placeholder(self):
        """Check if placeholder is unconditional (simplified heuristic)"""
        body = self.modifier_body
        
        # Very simplified check: if there's an if statement and _ is after it, it might be conditional
        # This is a heuristic and may have false positives/negatives
        
        # If _ appears before any if statement, it's unconditional
        if_pos = body.find('if')
        placeholder_pos = body.find('_;')
        
        if placeholder_pos >= 0 and if_pos >= 0:
            # If placeholder comes before if, it's unconditional
            if placeholder_pos < if_pos:
                return True
            else:
                return False
        elif placeholder_pos >= 0:
            # No if statement, placeholder exists
            return True
        
        return False

    def get_violations(self):
        """Return all detected violations"""
        return self.violations
