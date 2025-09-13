from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class ImproperContractArchitectureDetector(SolidityParserListener):
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.function_count = 0
        self.state_variable_count = 0
        self.modifier_count = 0
        self.event_count = 0
        self.struct_count = 0
        self.enum_count = 0
        self.mapping_count = 0
        self.function_complexity_score = 0
        self.has_proxy_pattern = False
        self.has_inheritance = False
        self.contract_concerns = set()  # Track different types of functionality
        
    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.function_count = 0
        self.state_variable_count = 0
        self.modifier_count = 0
        self.event_count = 0
        self.struct_count = 0
        self.enum_count = 0
        self.mapping_count = 0
        self.function_complexity_score = 0
        self.has_proxy_pattern = False
        self.has_inheritance = False
        self.contract_concerns = set()

    def exitContractDefinition(self, ctx):
        if not self.current_contract:
            return
            
        line = ctx.start.line
        
        # Check for monolithic design (too many functions)
        if self.function_count > 15:
            self.violations.append(
                f"❌ Monolithic contract detected in '{self.current_contract}' at line {line}: "
                f"Contract has {self.function_count} functions, suggesting poor separation of concerns. "
                f"Consider breaking into smaller, focused contracts."
            )
        
        # Check for excessive state variables
        if self.state_variable_count > 20:
            self.violations.append(
                f"❌ Excessive state variables in '{self.current_contract}' at line {line}: "
                f"Contract has {self.state_variable_count} state variables, indicating potential "
                f"monolithic design. Consider separating concerns into different contracts."
            )
        
        # Check for mixed concerns (multiple types of functionality)
        if len(self.contract_concerns) > 3:
            concerns_list = ", ".join(self.contract_concerns)
            self.violations.append(
                f"❌ Mixed concerns detected in '{self.current_contract}' at line {line}: "
                f"Contract handles multiple concerns: {concerns_list}. "
                f"Consider separating into focused contracts for better maintainability."
            )
        
        # Check for lack of modular design patterns
        if not self.has_inheritance and self.function_count > 10:
            self.violations.append(
                f"❌ Lack of modular design in '{self.current_contract}' at line {line}: "
                f"Large contract ({self.function_count} functions) without inheritance or modular patterns. "
                f"Consider using inheritance, libraries, or proxy patterns for better architecture."
            )
        
        # Check for missing upgradeability patterns
        if self.function_count > 8 and not self.has_proxy_pattern:
            self.violations.append(
                f"❌ Missing upgradeability pattern in '{self.current_contract}' at line {line}: "
                f"Contract lacks proxy pattern or upgrade mechanism. "
                f"Consider implementing upgradeable patterns for better maintainability."
            )
        
        # Check for high complexity score
        if self.function_complexity_score > 50:
            self.violations.append(
                f"❌ High complexity detected in '{self.current_contract}' at line {line}: "
                f"Complexity score: {self.function_complexity_score}. "
                f"High complexity increases attack surface and maintenance difficulty."
            )

    def enterFunctionDefinition(self, ctx):
        self.function_count += 1
        function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        
        # Analyze function for complexity and concerns
        self._analyze_function_concerns(function_name, ctx)
        
        # Calculate function complexity (simple heuristic)
        complexity = self._calculate_function_complexity(ctx)
        self.function_complexity_score += complexity

    def enterStateVariableDeclaration(self, ctx):
        self.state_variable_count += 1
        var_type = ctx.typeName().getText() if ctx.typeName() else ""
        
        # Track mapping usage
        if "mapping" in var_type:
            self.mapping_count += 1

    def enterModifierDefinition(self, ctx):
        self.modifier_count += 1

    def enterEventDefinition(self, ctx):
        self.event_count += 1

    def enterStructDefinition(self, ctx):
        self.struct_count += 1

    def enterEnumDefinition(self, ctx):
        self.enum_count += 1

    def enterInheritanceSpecifierList(self, ctx):
        self.has_inheritance = True

    def _analyze_function_concerns(self, function_name, ctx):
        """Analyze what type of concern this function addresses"""
        func_text = ctx.getText().lower()
        
        # Financial operations
        if any(keyword in func_text for keyword in ['transfer', 'withdraw', 'deposit', 'balance', 'payable', 'wei', 'ether']):
            self.contract_concerns.add("Financial")
        
        # Access control
        if any(keyword in func_text for keyword in ['owner', 'admin', 'authorized', 'only', 'require', 'modifier']):
            self.contract_concerns.add("Access Control")
        
        # Data management
        if any(keyword in func_text for keyword in ['mapping', 'array', 'storage', 'memory', 'struct']):
            self.contract_concerns.add("Data Management")
        
        # Business logic
        if any(keyword in func_text for keyword in ['calculate', 'compute', 'process', 'validate', 'check']):
            self.contract_concerns.add("Business Logic")
        
        # Upgrade/Admin functions
        if any(keyword in func_text for keyword in ['upgrade', 'update', 'migrate', 'proxy', 'implementation']):
            self.contract_concerns.add("Upgrade/Admin")
            self.has_proxy_pattern = True
        
        # Event emission
        if 'emit' in func_text:
            self.contract_concerns.add("Event Management")

    def _calculate_function_complexity(self, ctx):
        """Calculate a simple complexity score for the function"""
        complexity = 0
        func_text = ctx.getText()
        
        # Count control structures
        complexity += func_text.count('if') * 2
        complexity += func_text.count('for') * 3
        complexity += func_text.count('while') * 3
        complexity += func_text.count('require') * 1
        complexity += func_text.count('assert') * 1
        complexity += func_text.count('revert') * 1
        
        # Count function calls
        complexity += func_text.count('(') * 0.5
        
        # Count state variable accesses
        complexity += func_text.count('this.') * 1
        
        return int(complexity)

    def get_violations(self):
        return self.violations
