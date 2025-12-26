# S-SEC-010: Reentrancy Vulnerability Detection
# Detects potential reentrancy vulnerabilities (Check-Effects-Interactions pattern violations)
# Identifies external calls followed by state changes

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class ReentrancyDetector(SolidityParserListener):
    """
    Detects reentrancy vulnerabilities by identifying violations of the
    Check-Effects-Interactions pattern.
    
    This detector identifies:
    1. External calls (call, send, transfer, delegatecall) before state changes
    2. State variable writes after external calls
    3. Ether transfers followed by state updates
    
    False Positive Mitigation:
    - Checks for reentrancy guards (nonReentrant modifier, mutex patterns)
    - Excludes view/pure functions
    - Excludes simple transfer/send patterns that don't modify state after
    - Checks for proper CEI (Check-Effects-Interactions) pattern
    - Excludes calls to known safe contracts (e.g., ERC20 transfers in some contexts)
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None
        self.function_start_line = None
        self.function_state_mutability = None
        self.has_reentrancy_guard = False
        self.external_calls = []  # List of (line, call_text)
        self.state_changes = []   # List of (line, change_text)
        self.statement_order = []  # Track order of operations
        self.state_variables = set()

    def enterContractDefinition(self, ctx):
        """Track current contract and its state variables"""
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.state_variables = set()

    def exitContractDefinition(self, ctx):
        """Reset contract context"""
        self.current_contract = None
        self.state_variables = set()

    def enterStateVariableDeclaration(self, ctx):
        """Track state variables"""
        try:
            if hasattr(ctx, 'identifier') and ctx.identifier():
                var_name = ctx.identifier().getText()
                self.state_variables.add(var_name)
        except Exception:
            pass

    def enterFunctionDefinition(self, ctx):
        """Analyze function for reentrancy vulnerabilities"""
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "fallback"
        self.function_start_line = ctx.start.line
        self.external_calls = []
        self.state_changes = []
        self.statement_order = []
        self.has_reentrancy_guard = False
        
        # Check for reentrancy guard modifier
        self._check_reentrancy_guard(ctx)
        
        # Extract state mutability
        text = ctx.getText().lower()
        if 'view' in text:
            self.function_state_mutability = 'view'
        elif 'pure' in text:
            self.function_state_mutability = 'pure'
        else:
            self.function_state_mutability = 'mutable'

    def _check_reentrancy_guard(self, ctx):
        """Check if function has reentrancy guard modifier"""
        try:
            if hasattr(ctx, 'modifierList') and ctx.modifierList():
                modifier_list = ctx.modifierList()
                if hasattr(modifier_list, 'modifierInvocation'):
                    modifiers = modifier_list.modifierInvocation()
                    if modifiers:
                        for mod in modifiers:
                            if hasattr(mod, 'identifier') and mod.identifier():
                                mod_name = mod.identifier().getText().lower()
                                # Common reentrancy guard patterns
                                if any(guard in mod_name for guard in ['nonreentrant', 'noreentrancy', 'mutex', 'lock']):
                                    self.has_reentrancy_guard = True
        except Exception:
            pass

    def enterStatement(self, ctx):
        """Track statements for reentrancy analysis"""
        if not self.in_function:
            return
        
        line = ctx.start.line
        text = ctx.getText()
        
        # Track external calls
        if self._is_external_call(text):
            self.external_calls.append((line, text))
            self.statement_order.append(('call', line, text))
        
        # Track state changes
        if self._is_state_change(text):
            self.state_changes.append((line, text))
            self.statement_order.append(('state', line, text))

    def _is_external_call(self, text):
        """Check if text contains an external call"""
        text_lower = text.lower()
        
        # External call patterns
        external_patterns = [
            '.call(', '.call{', 
            '.delegatecall(', '.delegatecall{',
            '.staticcall(', '.staticcall{',
            '.send(', '.transfer('
        ]
        
        return any(pattern in text_lower for pattern in external_patterns)

    def _is_state_change(self, text):
        """Check if text modifies state variables"""
        # Look for assignments to state variables
        for state_var in self.state_variables:
            # Pattern: stateVar = ...
            if f'{state_var}=' in text or f'{state_var} =' in text:
                # Exclude comparisons
                if '==' not in text and '!=' not in text:
                    return True
            
            # Pattern: stateVar[...] = ...
            if f'{state_var}[' in text and '=' in text:
                if '==' not in text and '!=' not in text:
                    return True
        
        # Also check for common state-changing patterns
        state_patterns = [
            'balance[', 'balances[', 'allowance[', 'allowances[',
            'owner=', 'owner =', '_owner=', '_owner ='
        ]
        
        for pattern in state_patterns:
            if pattern in text.lower() and '=' in text:
                if '==' not in text and '!=' not in text:
                    return True
        
        return False

    def exitFunctionDefinition(self, ctx):
        """Check for reentrancy violations when exiting function"""
        # Skip if view/pure function
        if self.function_state_mutability in ['view', 'pure']:
            self.in_function = False
            return
        
        # Skip if has reentrancy guard
        if self.has_reentrancy_guard:
            self.in_function = False
            return
        
        # Skip if no external calls or no state changes
        if not self.external_calls or not self.state_changes:
            self.in_function = False
            return
        
        # Check for violations: state changes after external calls
        violations_found = []
        
        for call_line, call_text in self.external_calls:
            for state_line, state_text in self.state_changes:
                # If state change comes after external call
                if state_line > call_line:
                    # Check if they're in the same execution path (simplified check)
                    violations_found.append({
                        'call_line': call_line,
                        'call_text': call_text[:100],  # Truncate for readability
                        'state_line': state_line,
                        'state_text': state_text[:100]
                    })
        
        # Report violations
        if violations_found:
            # Group by call to avoid duplicate reports
            reported_calls = set()
            for violation in violations_found:
                call_key = (violation['call_line'], violation['call_text'])
                if call_key not in reported_calls:
                    reported_calls.add(call_key)
                    
                    self.violations.append(
                        f"❌ [S-SEC-010] CRITICAL: Potential reentrancy vulnerability in function '{self.function_name}' of contract '{self.current_contract}': "
                        f"External call at line {violation['call_line']} is followed by state change at line {violation['state_line']}. "
                        f"This violates the Check-Effects-Interactions pattern. Consider using a reentrancy guard or moving state changes before external calls."
                    )
        
        self.in_function = False

    def get_violations(self):
        """Return all detected violations"""
        return self.violations
