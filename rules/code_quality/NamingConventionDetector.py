"""
Detector for Solidity naming convention violations.

This detector checks if the code follows Solidity's official naming conventions:
- Contracts, Structs, Events, Enums: CapWords (PascalCase)
- Functions, Variables, Modifiers: mixedCase (camelCase)
- Constants: UPPER_CASE_WITH_UNDERSCORES
- Private/Internal: Can start with underscore
- State variables: Can use s_ prefix
- Immutable variables: Can use i_ prefix
"""

import re
from typing import List, Set
from antlr4 import ParserRuleContext
from parser.SolidityParser import SolidityParser
from rules.BaseDetector import BaseDetector, DetectorResult, Severity


class NamingConventionDetector(BaseDetector):
    """
    Detects violations of Solidity naming conventions.
    
    Follows the official Solidity style guide:
    https://docs.soliditylang.org/en/latest/style-guide.html#naming-conventions
    """

    def __init__(self):
        super().__init__(
            name="Naming Convention Violations",
            code="S-CQ-003",
            severity=Severity.INFO,
            description="Code does not follow Solidity naming conventions",
            recommendation="Follow the Solidity naming convention: CapWords for contracts/structs/events/enums, mixedCase for functions/variables/modifiers, UPPER_CASE_WITH_UNDERSCORES for constants."
        )
        self.current_contract = None
        self.violations: List[dict] = []

    # Naming pattern checkers
    @staticmethod
    def is_cap_words(name: str) -> bool:
        """Check if name follows CapWords (PascalCase) convention."""
        return re.search(r"^[A-Z]([A-Za-z0-9]+)?_?$", name) is not None

    @staticmethod
    def is_mixed_case(name: str) -> bool:
        """Check if name follows mixedCase (camelCase) convention."""
        return re.search(r"^[a-z]([A-Za-z0-9]+)?_?$", name) is not None

    @staticmethod
    def is_mixed_case_with_underscore(name: str) -> bool:
        """Check if name follows mixedCase with optional leading underscore."""
        return re.search(r"^[_]?[a-z]([A-Za-z0-9]+)?_?$", name) is not None

    @staticmethod
    def is_upper_case_with_underscores(name: str) -> bool:
        """Check if name follows UPPER_CASE_WITH_UNDERSCORES convention."""
        return re.search(r"^[A-Z0-9_]+_?$", name) is not None

    @staticmethod
    def is_state_naming(name: str) -> bool:
        """Check if name follows s_ prefix convention for state variables."""
        return re.search(r"^s_[a-z]([A-Za-z0-9]+)?_?$", name) is not None

    @staticmethod
    def is_immutable_naming(name: str) -> bool:
        """Check if name follows i_ prefix convention for immutable variables."""
        return re.search(r"^i_[a-z]([A-Za-z0-9]+)?_?$", name) is not None

    @staticmethod
    def should_avoid_name(name: str) -> bool:
        """Check if name is a single letter l, O, or I (easily confused)."""
        return re.search(r"^[lOI]$", name) is not None

    def enterContractDefinition(self, ctx: SolidityParser.ContractDefinitionContext):
        """Check contract naming convention."""
        if ctx.identifier():
            contract_name = ctx.identifier().getText()
            self.current_contract = contract_name
            
            if not self.is_cap_words(contract_name):
                self._add_violation(
                    ctx=ctx,
                    element_type="Contract",
                    element_name=contract_name,
                    expected_convention="CapWords (PascalCase)",
                    example="MyContract"
                )

    def exitContractDefinition(self, ctx: SolidityParser.ContractDefinitionContext):
        """Reset contract tracking."""
        self.current_contract = None

    def enterStructDefinition(self, ctx: SolidityParser.StructDefinitionContext):
        """Check struct naming convention."""
        if ctx.identifier():
            struct_name = ctx.identifier().getText()
            
            if not self.is_cap_words(struct_name):
                self._add_violation(
                    ctx=ctx,
                    element_type="Struct",
                    element_name=struct_name,
                    expected_convention="CapWords (PascalCase)",
                    example="MyStruct"
                )

    def enterEventDefinition(self, ctx: SolidityParser.EventDefinitionContext):
        """Check event naming convention."""
        if ctx.identifier():
            event_name = ctx.identifier().getText()
            
            if not self.is_cap_words(event_name):
                self._add_violation(
                    ctx=ctx,
                    element_type="Event",
                    element_name=event_name,
                    expected_convention="CapWords (PascalCase)",
                    example="TransferCompleted"
                )

    def enterEnumDefinition(self, ctx: SolidityParser.EnumDefinitionContext):
        """Check enum naming convention."""
        if ctx.identifier():
            enum_name = ctx.identifier().getText()
            
            if not self.is_cap_words(enum_name):
                self._add_violation(
                    ctx=ctx,
                    element_type="Enum",
                    element_name=enum_name,
                    expected_convention="CapWords (PascalCase)",
                    example="TokenState"
                )

    def enterFunctionDefinition(self, ctx: SolidityParser.FunctionDefinitionContext):
        """Check function naming convention."""
        if not ctx.functionDescriptor():
            return

        # Skip constructor, fallback, receive
        if ctx.functionDescriptor().getText() in ['constructor', 'fallback', 'receive']:
            return

        if ctx.functionDescriptor().identifier():
            func_name = ctx.functionDescriptor().identifier().getText()
            
            # Skip test functions (echidna_, crytic_)
            if func_name.startswith(('echidna_', 'crytic_')):
                return

            # Get visibility
            visibility = self._get_visibility(ctx)
            
            # Check naming
            if visibility in ['internal', 'private']:
                # Allow leading underscore for private/internal
                if not self.is_mixed_case_with_underscore(func_name):
                    self._add_violation(
                        ctx=ctx,
                        element_type="Function",
                        element_name=func_name,
                        expected_convention="mixedCase (camelCase), optionally with leading underscore",
                        example="_myFunction or myFunction"
                    )
            else:
                if not self.is_mixed_case(func_name):
                    self._add_violation(
                        ctx=ctx,
                        element_type="Function",
                        element_name=func_name,
                        expected_convention="mixedCase (camelCase)",
                        example="myFunction"
                    )

        # Check function parameters
        if ctx.parameterList():
            for param in ctx.parameterList().getTypedRuleContexts(SolidityParser.ParameterContext):
                if param.identifier():
                    param_name = param.identifier().getText()
                    
                    # Skip empty parameter names
                    if not param_name:
                        continue
                    
                    # Parameters should be mixedCase, optionally with leading underscore
                    if not self.is_mixed_case_with_underscore(param_name):
                        self._add_violation(
                            ctx=param,
                            element_type="Parameter",
                            element_name=param_name,
                            expected_convention="mixedCase (camelCase), optionally with leading underscore",
                            example="_amount or amount"
                        )

    def enterStateVariableDeclaration(self, ctx: SolidityParser.StateVariableDeclarationContext):
        """Check state variable naming convention."""
        if not ctx.identifier():
            return

        var_name = ctx.identifier().getText()
        
        # Check for confusing single-letter names
        if self.should_avoid_name(var_name):
            self._add_violation(
                ctx=ctx,
                element_type="Variable",
                element_name=var_name,
                expected_convention="Avoid single letters l, O, I (easily confused with 1, 0)",
                example="Use descriptive names instead"
            )
            return

        # Check if constant
        is_constant = self._is_constant(ctx)
        is_immutable = self._is_immutable(ctx)
        visibility = self._get_state_var_visibility(ctx)

        if is_constant:
            # ERC20 exceptions
            if var_name in ['symbol', 'name', 'decimals']:
                return
            
            # Public constants can be any case (for compatibility)
            if visibility == 'public':
                return
            
            # Private/internal constants should be UPPER_CASE
            if not self.is_upper_case_with_underscores(var_name):
                self._add_violation(
                    ctx=ctx,
                    element_type="Constant",
                    element_name=var_name,
                    expected_convention="UPPER_CASE_WITH_UNDERSCORES",
                    example="MAX_SUPPLY"
                )
        else:
            # Regular state variables
            if visibility in ['private', 'internal']:
                # Can use mixedCase, _mixedCase, s_mixedCase, or i_mixedCase
                correct_naming = (
                    self.is_mixed_case_with_underscore(var_name) or
                    self.is_state_naming(var_name)
                )
                
                if not correct_naming and is_immutable:
                    correct_naming = self.is_immutable_naming(var_name)
                
                if not correct_naming:
                    self._add_violation(
                        ctx=ctx,
                        element_type="State Variable",
                        element_name=var_name,
                        expected_convention="mixedCase, _mixedCase, s_mixedCase, or i_mixedCase (for immutable)",
                        example="s_balance or _balance or balance"
                    )
            else:
                # Public/external should be mixedCase
                if not self.is_mixed_case(var_name):
                    self._add_violation(
                        ctx=ctx,
                        element_type="State Variable",
                        element_name=var_name,
                        expected_convention="mixedCase (camelCase)",
                        example="totalSupply"
                    )

    def enterModifierDefinition(self, ctx: SolidityParser.ModifierDefinitionContext):
        """Check modifier naming convention."""
        if ctx.identifier():
            modifier_name = ctx.identifier().getText()
            
            if not self.is_mixed_case(modifier_name):
                self._add_violation(
                    ctx=ctx,
                    element_type="Modifier",
                    element_name=modifier_name,
                    expected_convention="mixedCase (camelCase)",
                    example="onlyOwner"
                )

    def _add_violation(self, ctx, element_type: str, element_name: str, 
                      expected_convention: str, example: str):
        """Add a naming convention violation."""
        line = ctx.start.line if ctx.start else 0
        
        self.add_result(DetectorResult(
            severity=self.severity,
            line=line,
            code=self.code,
            message=f"{element_type} '{element_name}' does not follow naming convention",
            details=(
                f"The {element_type.lower()} '{element_name}' does not follow Solidity naming conventions.\n\n"
                f"Expected: {expected_convention}\n"
                f"Example: {example}\n\n"
                f"Following naming conventions improves code readability and maintainability."
            ),
            recommendation=self.recommendation,
            contract=self.current_contract
        ))

    def _get_visibility(self, ctx: SolidityParser.FunctionDefinitionContext) -> str:
        """Extract function visibility."""
        if ctx.modifierList():
            for child in ctx.modifierList().children or []:
                text = child.getText()
                if text in ['public', 'external', 'internal', 'private']:
                    return text
        return 'public'

    def _get_state_var_visibility(self, ctx: SolidityParser.StateVariableDeclarationContext) -> str:
        """Extract state variable visibility."""
        text = ctx.getText()
        if 'public' in text:
            return 'public'
        elif 'external' in text:
            return 'external'
        elif 'internal' in text:
            return 'internal'
        elif 'private' in text:
            return 'private'
        return 'internal'  # Default

    def _is_constant(self, ctx: SolidityParser.StateVariableDeclarationContext) -> bool:
        """Check if state variable is constant."""
        text = ctx.getText()
        return 'constant' in text

    def _is_immutable(self, ctx: SolidityParser.StateVariableDeclarationContext) -> bool:
        """Check if state variable is immutable."""
        text = ctx.getText()
        return 'immutable' in text
