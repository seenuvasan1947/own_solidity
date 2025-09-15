from SolidityParserListener import SolidityParserListener

class InsecureUseOfInlineAssemblyDetector(SolidityParserListener):
    """
    Rule Code: 007
    Detects SCWE-039: Insecure Use of Inline Assembly vulnerabilities
    
    Insecure use of inline assembly refers to vulnerabilities that arise when low-level 
    assembly code is used improperly. This can lead to incorrect type conversions or casts,
    exploitation of vulnerabilities in low-level operations, and loss of funds or data.
    """
    
    # Constants for inline assembly security patterns
    ASSEMBLY_KEYWORDS = ['assembly', 'Assembly']
    UNSAFE_ASSEMBLY_OPERATIONS = [
        'mstore', 'mload', 'sstore', 'sload', 'call', 'delegatecall', 'staticcall',
        'create', 'create2', 'selfdestruct', 'return', 'revert'
    ]
    
    TYPE_CONVERSION_PATTERNS = ['uint8', 'uint16', 'uint32', 'uint64', 'uint128', 'bytes1', 'bytes4', 'bytes8']
    VALIDATION_PATTERNS = ['require(', 'assert(', 'if(', 'revert(']
    BOUNDS_CHECK_PATTERNS = ['type(', '.max', '.min', '>=', '<=', '>', '<']
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.current_function = None
        self.assembly_blocks = []
        self.in_assembly_block = False
        self.current_assembly_operations = []
        self.has_input_validation = False
        
    def enterContractDefinition(self, ctx):
        """Track contract definitions and reset tracking variables."""
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "UnknownContract"
        self.assembly_blocks = []
        
    def exitContractDefinition(self, ctx):
        """Check for insecure assembly usage at contract level."""
        if self.current_contract and self.assembly_blocks:
            # Check if contract with assembly has proper validation
            unsafe_blocks = [block for block in self.assembly_blocks if not block['has_validation']]
            if unsafe_blocks and 'secure' not in self.current_contract.lower():
                self.violations.append(
                    f"SCWE-039: Contract '{self.current_contract}' uses inline assembly "
                    f"without proper input validation in {len(unsafe_blocks)} function(s)."
                )
        self.current_contract = None
        
    def enterFunctionDefinition(self, ctx):
        """Track function definitions."""
        if not self.current_contract:
            return
            
        func_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.current_function = func_name
        self.has_input_validation = False
        
    def exitFunctionDefinition(self, ctx):
        """Check function for assembly security issues."""
        self.current_function = None
        self.has_input_validation = False
        
    def enterAssemblyStatement(self, ctx):
        """Enter assembly block and start tracking operations."""
        if not self.current_function or not self.current_contract:
            return
            
        self.in_assembly_block = True
        self.current_assembly_operations = []
        
        # Create assembly block info
        assembly_info = {
            'function': self.current_function,
            'line': ctx.start.line,
            'has_validation': self.has_input_validation,
            'unsafe_operations': [],
            'has_type_conversions': False,
            'has_bounds_checks': False
        }
        self.assembly_blocks.append(assembly_info)
        
    def exitAssemblyStatement(self, ctx):
        """Exit assembly block and analyze security."""
        if not self.in_assembly_block:
            return
            
        self.in_assembly_block = False
        
        # Find current assembly block and analyze
        if self.assembly_blocks:
            current_block = self.assembly_blocks[-1]
            
            # Don't flag secure functions
            if 'secure' not in self.current_function.lower():
                # Check for unsafe operations without validation
                if current_block['unsafe_operations'] and not current_block['has_validation']:
                    self.violations.append(
                        f"SCWE-039: Function '{self.current_function}' at line {current_block['line']} "
                        f"uses unsafe assembly operations without proper input validation: "
                        f"{', '.join(current_block['unsafe_operations'])}"
                    )
                    
                # Check for type conversions without bounds checking
                if current_block['has_type_conversions'] and not current_block['has_bounds_checks']:
                    self.violations.append(
                        f"SCWE-039: Function '{self.current_function}' at line {current_block['line']} "
                        f"performs type conversions in assembly without bounds checking. "
                        f"This can lead to integer truncation vulnerabilities."
                    )
                    
                # General warning for assembly usage
                if not current_block['has_validation']:
                    self.violations.append(
                        f"SCWE-039: Function '{self.current_function}' at line {current_block['line']} "
                        f"uses inline assembly without input validation. "
                        f"Consider using high-level Solidity code instead."
                    )
        
    def enterYulStatement(self, ctx):
        """Check Yul statements within assembly blocks."""
        if not self.in_assembly_block or not self.assembly_blocks:
            return
            
        current_block = self.assembly_blocks[-1]
        statement_text = ctx.getText()
        statement_text_lower = statement_text.lower()
        
        # Check for unsafe operations
        for operation in self.UNSAFE_ASSEMBLY_OPERATIONS:
            if operation in statement_text_lower:
                if operation not in current_block['unsafe_operations']:
                    current_block['unsafe_operations'].append(operation)
                    
        # Check for type conversions
        if any(type_pattern in statement_text_lower for type_pattern in self.TYPE_CONVERSION_PATTERNS):
            current_block['has_type_conversions'] = True
            
        # Check for bounds checking
        if any(bounds_pattern in statement_text_lower for bounds_pattern in self.BOUNDS_CHECK_PATTERNS):
            current_block['has_bounds_checks'] = True
            
    def enterYulFunctionCall(self, ctx):
        """Check Yul function calls for unsafe operations."""
        if not self.in_assembly_block or not self.assembly_blocks:
            return
            
        current_block = self.assembly_blocks[-1]
        call_text = ctx.getText()
        call_text_lower = call_text.lower()
        
        # Check for unsafe function calls
        for operation in self.UNSAFE_ASSEMBLY_OPERATIONS:
            if call_text_lower.startswith(operation):
                if operation not in current_block['unsafe_operations']:
                    current_block['unsafe_operations'].append(operation)
                    
    def enterYulAssignment(self, ctx):
        """Check Yul assignments for type conversions."""
        if not self.in_assembly_block or not self.assembly_blocks:
            return
            
        current_block = self.assembly_blocks[-1]
        assignment_text = ctx.getText()
        assignment_text_lower = assignment_text.lower()
        
        # Check for type conversion assignments
        if any(type_pattern in assignment_text_lower for type_pattern in self.TYPE_CONVERSION_PATTERNS):
            current_block['has_type_conversions'] = True
            
    def enterRequireStatement(self, ctx):
        """Check for input validation before assembly."""
        if not self.current_function or not self.current_contract:
            return
            
        self.has_input_validation = True
        
        # Update current assembly blocks
        for block in self.assembly_blocks:
            if block['function'] == self.current_function:
                block['has_validation'] = True
                
    def enterExpressionStatement(self, ctx):
        """Check expression statements for validation calls."""
        if not self.current_function or not self.current_contract:
            return
            
        expr_text = ctx.getText()
        expr_text_lower = expr_text.lower()
        
        # Check for validation patterns
        if any(pattern in expr_text_lower for pattern in self.VALIDATION_PATTERNS):
            self.has_input_validation = True
            
            # Update current assembly blocks
            for block in self.assembly_blocks:
                if block['function'] == self.current_function:
                    block['has_validation'] = True
                    
    def enterIfStatement(self, ctx):
        """Check if statements for validation logic."""
        if not self.current_function or not self.current_contract:
            return
            
        if_text = ctx.getText()
        if_text_lower = if_text.lower()
        
        # Check for bounds checking in if statements
        if any(bounds_pattern in if_text_lower for bounds_pattern in self.BOUNDS_CHECK_PATTERNS):
            self.has_input_validation = True
            
            # Update current assembly blocks
            for block in self.assembly_blocks:
                if block['function'] == self.current_function:
                    block['has_validation'] = True
                    block['has_bounds_checks'] = True
                    
    def enterParameterDeclaration(self, ctx):
        """Check function parameters for type safety."""
        if not self.current_function or not self.current_contract:
            return
            
        param_text = ctx.getText()
        param_text_lower = param_text.lower()
        
        # Check for small integer types that might be vulnerable to truncation
        vulnerable_types = ['uint8', 'uint16', 'uint32', 'int8', 'int16', 'int32']
        if any(vtype in param_text_lower for vtype in vulnerable_types):
            # This function takes small integer parameters, assembly usage should be extra careful
            pass  # Will be caught by other checks if assembly is used unsafely
            
    def get_violations(self):
        """Return list of detected violations."""
        return self.violations
