# S-SEC-022: Right-To-Left Override Character Detection
# Detects usage of Unicode RTLO character (U+202E) which can hide malicious code
# Attackers can use this to make code appear different than it actually is

from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener
import re

class RTLODetector(SolidityParserListener):
    
    # Right-To-Left Override character
    RTLO_CHARACTER = '\u202e'
    RTLO_CHARACTER_ENCODED = RTLO_CHARACTER.encode('utf-8')
    
    def __init__(self):
        self.violations = []
        self.current_file = "unknown"
        self.source_code = ""

    def set_source(self, filename, source_code):
        """Set the current file and source code being analyzed"""
        self.current_file = filename
        self.source_code = source_code

    def detect_rtlo(self):
        """Detect RTLO characters in the source code"""
        if not self.source_code:
            return
        
        source_encoded = self.source_code.encode('utf-8')
        start_index = 0
        
        # Search for all RTLO characters
        while True:
            result_index = source_encoded[start_index:].find(self.RTLO_CHARACTER_ENCODED)
            
            if result_index == -1:
                break
            
            # Found RTLO character
            idx = start_index + result_index
            
            # Get context around the character
            context_start = max(0, idx - 50)
            context_end = min(len(source_encoded), idx + 50)
            context = source_encoded[context_start:context_end]
            
            # Calculate line number
            line_num = self.source_code[:idx].count('\n') + 1
            
            self.violations.append(
                f"❌ [S-SEC-022] HIGH: Right-To-Left Override character detected in {self.current_file} at byte offset {idx} (line ~{line_num}): "
                f"Unicode RTLO character (U+202E) found. This can be used to hide malicious code by reversing text display. "
                f"Context: {context.decode('utf-8', errors='replace')}\n"
                f"Remove this character immediately - it may indicate an attack attempt."
            )
            
            start_index = idx + 1

    def get_violations(self):
        """Return all detected violations"""
        self.detect_rtlo()
        return self.violations
