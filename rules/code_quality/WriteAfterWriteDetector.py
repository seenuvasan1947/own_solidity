# S-CODE-033: Write After Write
# Detects variables written twice without being read in between
# First write is wasted, indicates logic error

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class WriteAfterWriteDetector(SolidityParserListener):
    
    def __init__(self):
        self.violations = []
        self.current_contract = None
        self.in_function = False
        self.function_name = None
        self.function_body = []
        self.written_vars = {}  # {var_name: line}

    def enterContractDefinition(self, ctx):
        self.current_contract = ctx.identifier().getText() if ctx.identifier() else "unknown"

    def exitContractDefinition(self, ctx):
        self.current_contract = None

    def enterFunctionDefinition(self, ctx):
        self.in_function = True
        self.function_name = ctx.identifier().getText() if ctx.identifier() else "unknown"
        self.function_body = []
        self.written_vars = {}

    def exitFunctionDefinition(self, ctx):
        self._analyze_writes()
        self.in_function = False
        self.function_name = None

    def enterStatement(self, ctx):
        if self.in_function:
            stmt_text = ctx.getText()
            line = ctx.start.line
            self.function_body.append((line, stmt_text))

    def _analyze_writes(self):
        """Analyze function body for write-after-write patterns"""
        written = {}  # {var_name: first_write_line}
        
        for line, stmt in self.function_body:
            # Extract variable writes (assignments)
            write_matches = re.finditer(r'(\w+)\s*=\s*[^=]', stmt)
            for match in write_matches:
                var_name = match.group(1)
                
                # Skip type names and keywords
                if var_name in ['uint', 'uint256', 'int', 'address', 'bool', 'bytes', 'string', 'memory', 'storage']:
                    continue
                
                # Check if variable was written before without being read
                if var_name in written:
                    # Check if variable was read between writes
                    was_read = self._was_read_between(var_name, written[var_name], line)
                    
                    if not was_read:
                        # Avoid FP: skip initialization to zero pattern (uint a = 0; a = 10;)
                        first_stmt = next((s for l, s in self.function_body if l == written[var_name]), "")
                        if not re.search(rf'{var_name}\s*=\s*0\b', first_stmt):
                            self.violations.append(
                                f"⚠️  [S-CODE-033] MEDIUM: Write after write in function '{self.function_name}' of contract '{self.current_contract}': "
                                f"Variable '{var_name}' written at line {written[var_name]} and again at line {line} without being read. "
                                f"First write is wasted. Check for logic error."
                            )
                
                written[var_name] = line
            
            # Track variable reads
            # Simple heuristic: if variable appears but not in assignment context
            for var_name in list(written.keys()):
                # Check if variable is read (appears in non-assignment context)
                if re.search(rf'\b{var_name}\b', stmt) and not re.search(rf'{var_name}\s*=', stmt):
                    # Variable was read, remove from written tracking
                    del written[var_name]

    def _was_read_between(self, var_name, first_line, second_line):
        """Check if variable was read between two writes"""
        for line, stmt in self.function_body:
            if first_line < line < second_line:
                # Check if variable appears in non-assignment context
                if re.search(rf'\b{var_name}\b', stmt) and not re.search(rf'{var_name}\s*=', stmt):
                    return True
        return False

    def get_violations(self):
        return self.violations
