from rules.VulnerableCryptographicAlgorithmsDetector import VulnerableCryptographicAlgorithmsDetector
from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser

input_stream = FileStream('test/ComprehensiveTestSCWE027-032.sol')
lexer = SolidityLexer(input_stream)
stream = CommonTokenStream(lexer)
parser = SolidityParser(stream)
tree = parser.sourceUnit()
walker = ParseTreeWalker()
detector = VulnerableCryptographicAlgorithmsDetector()
walker.walk(detector, tree)
print('SCWE-027 Violations:', len(detector.get_violations()))
for v in detector.get_violations():
    print(v)
