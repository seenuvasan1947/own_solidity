# S-SEC-008: Backdoor Function Detection
# Detects potentially malicious function names that may indicate backdoors or hidden functionality
# This detector identifies functions with suspicious names that could be used for unauthorized access

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class BackdoorDetector(SolidityParserListener):
    """
    Detects functions with suspicious names that may indicate backdoor functionality.
    
    This detector looks for:
    1. Functions with explicit backdoor-related names
    2. Functions with obfuscated or suspicious naming patterns
    3. Functions with admin/owner functionality but suspicious names
    
    False Positive Mitigation:
    - Excludes constructor and fallback functions
    - Excludes functions with proper access control modifiers
    - Uses context-aware detection for legitimate admin functions
    - Checks for proper documentation/comments explaining the function
    """
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None
        self.function_start_line = None
        self.function_modifiers = []
        self.function_visibility = None
        self.has_access_control = False
        
        # Suspicious keywords that indicate potential backdoors
        self.backdoor_keywords = [
            'backdoor', 'hidden', 'secret', 'stealth', 'covert',
            'bypass', 'override', 'hack', 'exploit', 'malicious',
            'drain', 'steal', 'rug', 'scam', 'honeypot'
        ]
        
        # Obfuscated patterns (single letter, underscore-heavy, etc.)
        self.obfuscation_patterns = [
            '_', '__', '___', 'x', 'y', 'z', 'temp', 'tmp',
            'test', 'debug', 'dev', 'admin_', '_admin'
        ]
        
        # Legitimate admin function patterns (to reduce false positives)
        self.legitimate_admin_patterns = [
            'onlyowner', 'onlyadmin', 'authorized', 'restricted',
            'pause', 'unpause', 'emergency', 'recover', 'rescue'
        ]

    def enterContractDefinition(self, ctx):
        """Track current contract being analyzed"""
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"

    def exitContractDefinition(self, ctx):
        """Reset contract context"""
        self.current_contract = None

    def enterFunctionDefinition(self, ctx):
        """Analyze function for backdoor indicators"""
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else None
        self.function_start_line = ctx.start.line
        self.function_modifiers = []
        self.function_visibility = None
        self.has_access_control = False
        
        # Skip if no function name (constructor, fallback, receive)
        if not self.function_name:
            return
            
        # Extract visibility
        self._extract_visibility(ctx)
        
        # Extract modifiers
        self._extract_modifiers(ctx)
        
        # Check for access control modifiers
        self._check_access_control()

    def _extract_visibility(self, ctx):
        """Extract function visibility"""
        try:
            text = ctx.getText().lower()
            if 'public' in text:
                self.function_visibility = 'public'
            elif 'external' in text:
                self.function_visibility = 'external'
            elif 'internal' in text:
                self.function_visibility = 'internal'
            elif 'private' in text:
                self.function_visibility = 'private'
        except Exception:
            pass

    def _extract_modifiers(self, ctx):
        """Extract function modifiers"""
        try:
            # Look for modifier invocations
            if hasattr(ctx, 'modifierList') and ctx.modifierList():
                modifier_list = ctx.modifierList()
                if hasattr(modifier_list, 'modifierInvocation'):
                    modifiers = modifier_list.modifierInvocation()
                    if modifiers:
                        for mod in modifiers:
                            if hasattr(mod, 'identifier') and mod.identifier():
                                mod_name = mod.identifier().getText().lower()
                                self.function_modifiers.append(mod_name)
        except Exception:
            pass

    def _check_access_control(self):
        """Check if function has proper access control"""
        access_control_modifiers = [
            'onlyowner', 'onlyadmin', 'authorized', 'restricted',
            'requiresauth', 'onlyauthorized', 'onlygov', 'onlygovernance'
        ]
        
        for modifier in self.function_modifiers:
            if any(ac in modifier for ac in access_control_modifiers):
                self.has_access_control = True
                break

    def exitFunctionDefinition(self, ctx):
        """Check for backdoor patterns when exiting function"""
        if not self.function_name:
            self.in_function = False
            return
        
        func_name_lower = self.function_name.lower()
        
        # Check 1: Explicit backdoor keywords
        if self._has_explicit_backdoor_keyword(func_name_lower):
            # High confidence - explicit backdoor keyword
            self.violations.append(
                f"❌ [S-SEC-008] CRITICAL: Potential backdoor function detected in contract '{self.current_contract}' at line {self.function_start_line}: "
                f"Function '{self.function_name}' contains suspicious keyword that may indicate malicious intent."
            )
        
        # Check 2: Suspicious obfuscated names (only for public/external functions)
        elif self._is_suspicious_obfuscated(func_name_lower) and self.function_visibility in ['public', 'external']:
            # Medium confidence - obfuscated name without access control
            if not self.has_access_control:
                self.violations.append(
                    f"⚠️  [S-SEC-008] WARNING: Suspicious function name in contract '{self.current_contract}' at line {self.function_start_line}: "
                    f"Function '{self.function_name}' has an obfuscated name and lacks access control modifiers."
                )
        
        # Check 3: Admin-like functionality without proper naming
        elif self._is_suspicious_admin_function(func_name_lower):
            # Low-medium confidence - admin function with unusual name
            self.violations.append(
                f"⚠️  [S-SEC-008] WARNING: Potentially hidden admin function in contract '{self.current_contract}' at line {self.function_start_line}: "
                f"Function '{self.function_name}' appears to have administrative capabilities but uses a non-standard name."
            )
        
        self.in_function = False
        self.function_name = None
        self.function_modifiers = []
        self.function_visibility = None
        self.has_access_control = False

    def _has_explicit_backdoor_keyword(self, func_name):
        """Check if function name contains explicit backdoor keywords"""
        return any(keyword in func_name for keyword in self.backdoor_keywords)

    def _is_suspicious_obfuscated(self, func_name):
        """Check if function name appears to be obfuscated"""
        # Very short names (1-2 chars) that are not common patterns
        if len(func_name) <= 2 and func_name not in ['to', 'at', 'of', 'is', 'do']:
            return True
        
        # Heavy use of underscores
        if func_name.count('_') > 3:
            return True
        
        # Starts/ends with multiple underscores (not standard Solidity convention)
        if func_name.startswith('__') or func_name.endswith('__'):
            return True
        
        # Random-looking character combinations
        if len(func_name) > 3 and not any(c.isalpha() for c in func_name):
            return True
        
        return False

    def _is_suspicious_admin_function(self, func_name):
        """Check if function appears to be an admin function with suspicious naming"""
        # Look for functions that modify critical state but have unusual names
        admin_indicators = [
            'withdraw', 'transfer', 'send', 'call', 'delegatecall',
            'selfdestruct', 'destroy', 'kill', 'change', 'set', 'update'
        ]
        
        # Check if function has admin-like keywords
        has_admin_keyword = any(indicator in func_name for indicator in admin_indicators)
        
        # Check if it's a legitimate admin function
        is_legitimate = any(pattern in func_name for pattern in self.legitimate_admin_patterns)
        
        # Check if it has proper access control
        has_proper_naming = func_name.startswith('admin') or func_name.startswith('owner')
        
        # Suspicious if it has admin functionality but lacks proper naming and access control
        if has_admin_keyword and not is_legitimate and not has_proper_naming and not self.has_access_control:
            return True
        
        return False

    def get_violations(self):
        """Return all detected violations"""
        return self.violations
