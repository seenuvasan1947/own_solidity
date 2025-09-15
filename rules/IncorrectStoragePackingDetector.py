from SolidityParserListener import SolidityParserListener

class IncorrectStoragePackingDetector(SolidityParserListener):
    """
    Rule Code: 008
    Detects SCWE-040: Incorrect Storage Packing vulnerabilities
    
    Incorrect storage packing in Solidity occurs when storage variables are not efficiently 
    packed within a single storage slot, leading to unnecessary gas consumption. Solidity 
    automatically stores variables in 32-byte (256-bit) slots, and inefficient ordering 
    of data types can lead to wasted space.
    """
    
    # Constants for storage packing analysis
    STORAGE_SIZES = {
        'bool': 1,
        'uint8': 1, 'int8': 1,
        'uint16': 2, 'int16': 2,
        'uint24': 3, 'int24': 3,
        'uint32': 4, 'int32': 4,
        'uint40': 5, 'int40': 5,
        'uint48': 6, 'int48': 6,
        'uint56': 7, 'int56': 7,
        'uint64': 8, 'int64': 8,
        'uint72': 9, 'int72': 9,
        'uint80': 10, 'int80': 10,
        'uint88': 11, 'int88': 11,
        'uint96': 12, 'int96': 12,
        'uint104': 13, 'int104': 13,
        'uint112': 14, 'int112': 14,
        'uint120': 15, 'int120': 15,
        'uint128': 16, 'int128': 16,
        'uint136': 17, 'int136': 17,
        'uint144': 18, 'int144': 18,
        'uint152': 19, 'int152': 19,
        'uint160': 20, 'int160': 20,
        'uint168': 21, 'int168': 21,
        'uint176': 22, 'int176': 22,
        'uint184': 23, 'int184': 23,
        'uint192': 24, 'int192': 24,
        'uint200': 25, 'int200': 25,
        'uint208': 26, 'int208': 26,
        'uint216': 27, 'int216': 27,
        'uint224': 28, 'int224': 28,
        'uint232': 29, 'int232': 29,
        'uint240': 30, 'int240': 30,
        'uint248': 31, 'int248': 31,
        'uint256': 32, 'int256': 32, 'uint': 32, 'int': 32,
        'bytes1': 1, 'bytes2': 2, 'bytes3': 3, 'bytes4': 4,
        'bytes5': 5, 'bytes6': 6, 'bytes7': 7, 'bytes8': 8,
        'bytes9': 9, 'bytes10': 10, 'bytes11': 11, 'bytes12': 12,
        'bytes13': 13, 'bytes14': 14, 'bytes15': 15, 'bytes16': 16,
        'bytes17': 17, 'bytes18': 18, 'bytes19': 19, 'bytes20': 20,
        'bytes21': 21, 'bytes22': 22, 'bytes23': 23, 'bytes24': 24,
        'bytes25': 25, 'bytes26': 26, 'bytes27': 27, 'bytes28': 28,
        'bytes29': 29, 'bytes30': 30, 'bytes31': 31, 'bytes32': 32,
        'address': 20,
        'bytes': 32, 'string': 32  # Dynamic types take full slot for length
    }
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.state_variables = []
        self.current_variable_index = 0
        
    def enterContractDefinition(self, ctx):
        """Track contract definitions and reset tracking variables."""
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "UnknownContract"
        self.state_variables = []
        self.current_variable_index = 0
        
    def exitContractDefinition(self, ctx):
        """Analyze storage packing efficiency at contract level."""
        if self.current_contract and self.state_variables:
            # Don't analyze optimized contracts
            if 'optimized' not in self.current_contract.lower():
                self._analyze_storage_packing()
        self.current_contract = None
        
    def enterStateVariableDeclaration(self, ctx):
        """Track state variable declarations for storage analysis."""
        if not self.current_contract:
            return
            
        var_name = ctx.identifier().getText() if ctx.identifier() else f"var_{self.current_variable_index}"
        var_line = ctx.start.line
        
        # Get variable type
        type_ctx = ctx.typeName()
        var_type = self._extract_type_name(type_ctx) if type_ctx else "unknown"
        
        # Store variable info
        var_info = {
            'name': var_name,
            'type': var_type,
            'line': var_line,
            'index': self.current_variable_index,
            'size': self._get_type_size(var_type)
        }
        
        self.state_variables.append(var_info)
        self.current_variable_index += 1
        
    def _extract_type_name(self, type_ctx):
        """Extract type name from type context."""
        if not type_ctx:
            return "unknown"
            
        type_text = type_ctx.getText()
        
        # Handle array types - they take full slots
        if '[' in type_text and ']' in type_text:
            return type_text.split('[')[0]  # Get base type
            
        # Handle mapping types - they take full slots
        if type_text.startswith('mapping'):
            return 'mapping'
            
        return type_text
        
    def _get_type_size(self, type_name):
        """Get the storage size of a type in bytes."""
        # Handle array and mapping types
        if '[' in type_name or type_name == 'mapping':
            return 32  # Arrays and mappings take full slots
            
        # Handle address payable
        if 'address' in type_name:
            return 20
            
        # Look up in storage sizes
        return self.STORAGE_SIZES.get(type_name, 32)
        
    def _analyze_storage_packing(self):
        """Analyze storage packing efficiency and detect issues."""
        if len(self.state_variables) < 2:
            return  # Need at least 2 variables to have packing issues
            
        # Simulate storage slot allocation
        slots = []
        current_slot_usage = 0
        current_slot_vars = []
        
        for var in self.state_variables:
            var_size = var['size']
            
            # If variable takes full slot or doesn't fit in current slot
            if var_size == 32 or current_slot_usage + var_size > 32:
                # Finalize current slot if it has variables
                if current_slot_vars:
                    slots.append({
                        'variables': current_slot_vars.copy(),
                        'usage': current_slot_usage,
                        'waste': 32 - current_slot_usage
                    })
                
                # Start new slot
                current_slot_vars = [var]
                current_slot_usage = var_size
            else:
                # Add to current slot
                current_slot_vars.append(var)
                current_slot_usage += var_size
                
        # Finalize last slot
        if current_slot_vars:
            slots.append({
                'variables': current_slot_vars.copy(),
                'usage': current_slot_usage,
                'waste': 32 - current_slot_usage
            })
            
        # Analyze for inefficiencies
        self._detect_packing_inefficiencies(slots)
        
    def _detect_packing_inefficiencies(self, slots):
        """Detect and report storage packing inefficiencies."""
        total_waste = sum(slot['waste'] for slot in slots)
        
        # Report significant waste
        if total_waste > 32:  # More than one slot worth of waste
            self.violations.append(
                f"SCWE-040: Contract '{self.current_contract}' has inefficient storage packing "
                f"with {total_waste} bytes wasted across {len(slots)} slots. "
                f"Consider reordering state variables to optimize gas usage."
            )
            
        # Check for specific inefficient patterns
        for i, slot in enumerate(slots):
            if slot['waste'] > 16:  # More than half a slot wasted
                var_names = [var['name'] for var in slot['variables']]
                self.violations.append(
                    f"SCWE-040: Storage slot {i} in contract '{self.current_contract}' "
                    f"wastes {slot['waste']} bytes. Variables: {', '.join(var_names)}. "
                    f"Consider grouping smaller types together."
                )
                
        # Detect specific anti-patterns
        self._detect_packing_antipatterns()
        
    def _detect_packing_antipatterns(self):
        """Detect common storage packing anti-patterns."""
        if len(self.state_variables) < 3:
            return
            
        # Pattern 1: Large type between small types
        for i in range(1, len(self.state_variables) - 1):
            prev_var = self.state_variables[i - 1]
            curr_var = self.state_variables[i]
            next_var = self.state_variables[i + 1]
            
            # If current variable is large and surrounded by small variables
            if (curr_var['size'] == 32 and 
                prev_var['size'] < 32 and next_var['size'] < 32 and
                prev_var['size'] + next_var['size'] <= 32):
                
                self.violations.append(
                    f"SCWE-040: Variable '{curr_var['name']}' at line {curr_var['line']} "
                    f"separates small variables '{prev_var['name']}' and '{next_var['name']}' "
                    f"that could be packed together. Consider reordering."
                )
                
        # Pattern 2: Multiple small variables that could be grouped
        small_vars = [var for var in self.state_variables if var['size'] < 16]
        if len(small_vars) >= 3:
            # Check if they are not consecutive
            consecutive_groups = []
            current_group = [small_vars[0]]
            
            for i in range(1, len(small_vars)):
                if small_vars[i]['index'] == small_vars[i-1]['index'] + 1:
                    current_group.append(small_vars[i])
                else:
                    if len(current_group) >= 2:
                        consecutive_groups.append(current_group)
                    current_group = [small_vars[i]]
                    
            if len(current_group) >= 2:
                consecutive_groups.append(current_group)
                
            # If we have scattered small variables
            scattered_small = len(small_vars) - sum(len(group) for group in consecutive_groups)
            if scattered_small >= 2:
                scattered_names = [var['name'] for var in small_vars if not any(var in group for group in consecutive_groups)]
                if scattered_names:
                    self.violations.append(
                        f"SCWE-040: Contract '{self.current_contract}' has scattered small variables "
                        f"that could be grouped for better packing: {', '.join(scattered_names[:3])}{'...' if len(scattered_names) > 3 else ''}. "
                        f"Consider moving them together."
                    )
                    
        # Pattern 3: Bool variables not grouped together
        bool_vars = [var for var in self.state_variables if var['type'] == 'bool']
        if len(bool_vars) >= 2:
            # Check if bool variables are scattered
            bool_indices = [var['index'] for var in bool_vars]
            max_gap = max(bool_indices) - min(bool_indices)
            
            if max_gap > len(bool_vars):  # Bools are scattered
                bool_names = [var['name'] for var in bool_vars]
                self.violations.append(
                    f"SCWE-040: Contract '{self.current_contract}' has scattered boolean variables "
                    f"{', '.join(bool_names)} that could be grouped together to save gas. "
                    f"Multiple bools can share a single storage slot."
                )
                
    def get_violations(self):
        """Return list of detected violations."""
        return self.violations
