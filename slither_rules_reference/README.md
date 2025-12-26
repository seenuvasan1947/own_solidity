# Slither Rules Reference

This folder contains all detector rules from Slither for future reference and integration.

## Purpose
- Reference implementation of various Solidity vulnerability detectors
- Pick and adapt rules one by one for our ANTLR-based tool
- Learn patterns and detection strategies from Slither

## Structure
The detectors are organized by category (same as Slither's structure):
- **attributes/** - Contract attribute detectors
- **compiler_bugs/** - Solidity compiler bug detectors  
- **erc/** - ERC standard compliance detectors
- **functions/** - Function-level detectors
- **operations/** - Operation-level detectors
- **reentrancy/** - Reentrancy vulnerability detectors
- **shadowing/** - Variable shadowing detectors
- **statements/** - Statement-level detectors
- **variables/** - Variable-related detectors
- And more...

## How to Use
1. Browse the detectors to find interesting patterns
2. Study the detection logic in each file
3. Adapt the logic to work with our ANTLR parser
4. Create a new detector in our `rules/` folder following our structure

## Note
These are Slither's original detectors - they use Slither's IR (Intermediate Representation).
We need to adapt the logic to work with ANTLR's parse tree structure.

## Integration Workflow
1. Choose a detector from this folder
2. Understand what vulnerability it detects
3. Create equivalent detector using ANTLR's SolidityParserListener
4. Test with sample contracts
5. Add to appropriate category in `rules/` folder
