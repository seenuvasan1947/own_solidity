# S-REEN-002: Reentrancy Read-Before-Write
# Detects reentrancy where state is read, external call made, then state written
# Can lead to logic errors even without ETH theft

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class ReentrancyReadBeforeWriteDetector(SolidityParserListener):
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None
        self.function_start_line = None
        self.function_body = []
        self.has_nonreentrant = False

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"

    def exitContractDefinition(self, ctx):
        self.current_contract = None

    def enterFunctionDefinition(self, ctx):
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.function_start_line = ctx.start.line
        self.function_body = []
        
        func_text = ctx.getText()
        self.has_nonreentrant = 'nonReentrant' in func_text

    def exitFunctionDefinition(self, ctx):
        if self.in_function and not self.has_nonreentrant:
            self._analyze_read_before_write()
        
        self.in_function = False
        self.function_name = None

    def enterStatement(self, ctx):
        if self.in_function:
            self.function_body.append((ctx.start.line, ctx.getText()))

    def _analyze_read_before_write(self):
        state_reads = {}
        external_calls = []
        state_writes = []
        
        for line, stmt in self.function_body:
            # Track state variable reads
            for var in self._extract_state_reads(stmt):
                if var not in state_reads:
                    state_reads[var] = line
            
            # Track external calls
            if self._is_external_call(stmt):
                external_calls.append(line)
            
            # Track state writes
            for var in self._extract_state_writes(stmt):
                state_writes.append((line, var))
        
        # Check pattern: read -> call -> write
        for write_line, write_var in state_writes:
            if write_var in state_reads:
                read_line = state_reads[write_var]
                
                # Check if there's an external call between read and write
                calls_between = [c for c in external_calls if read_line < c < write_line]
                
                if calls_between:
                    self.violations.append(
                        f"⚠️  [S-REEN-002] MEDIUM: Read-before-write reentrancy in function '{self.function_name}' of contract '{self.current_contract}': "
                        f"Variable '{write_var}' read at line {read_line}, external call at line {calls_between[0]}, then written at line {write_line}. "
                        f"Apply check-effects-interactions pattern."
                    )

    def _extract_state_reads(self, stmt):
        # Extract potential state variable reads
        reads = set()
        # Pattern: variable[...] or variable.member
        matches = re.finditer(r'(\w+)[\[\.]', stmt)
        for match in matches:
            var = match.group(1)
            if var not in ['msg', 'block', 'tx', 'this', 'super']:
                reads.add(var)
        return reads

    def _extract_state_writes(self, stmt):
        # Extract state variable writes
        writes = set()
        # Pattern: variable = ... or variable[...] = ...
        matches = re.finditer(r'(\w+)(?:\[.*\])?\s*=', stmt)
        for match in matches:
            var = match.group(1)
            if var not in ['msg', 'block', 'tx']:
                writes.add(var)
        return writes

    def _is_external_call(self, stmt):
        patterns = [r'\.call\s*[\(\{]', r'\.delegatecall\s*\(', r'\w+\.\w+\s*\(']
        if 'this.' in stmt or 'super.' in stmt:
            return False
        return any(re.search(p, stmt) for p in patterns)

    def get_violations(self):
        return self.violations
