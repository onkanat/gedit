# G-code Parser Enhancements

## Problem Statement

The current G-code parser in `app/gcode_parser.py` needs enhancements to better handle real-world G-code files and provide more robust parsing capabilities, inspired by patterns found in the Gerber2nc project.

## User Stories

### As a G-code developer

- I want the parser to better handle modal states so that commands persist correctly throughout the program
- I want improved arc processing with proper center calculations so that G2/G3 commands work reliably
- I want program structure detection so that initialization and termination sequences are recognized
- I want coordinate validation so that extreme values are flagged as warnings
- I want better error reporting so that parsing issues are clearly identified

## Requirements

### Functional Requirements

1. **Enhanced Modal State Management**
   - Initialize modal states with proper defaults (G0, G17, G21, G90, G94, G54)
   - Reset modal states on M30 (program end and rewind)
   - Track additional modal states like distance mode and coordinate system

2. **Improved Arc Processing**
   - Calculate arc centers from I/J/K offsets relative to start position
   - Prioritize R parameter over I/J/K when both are present
   - Validate arc parameters match the current work plane (G17/G18/G19)
   - Provide clearer error messages for invalid arc definitions

3. **Program Structure Detection**
   - Detect common initialization sequences (G17 G21 G90 G94 patterns)
   - Identify program termination (M30, M2)
   - Flag programs missing proper header/footer structure

4. **Coordinate Validation**
   - Warn about coordinates exceeding reasonable limits (configurable, default 1000mm)
   - Track coordinate system changes and their effects

5. **Enhanced Error Reporting**
   - Provide more context in diagnostic messages
   - Include suggestions for fixing common errors
   - Maintain backwards compatibility with existing diagnostic structure

### Non-Functional Requirements

1. **Performance**: Parser should handle files up to 100K lines without noticeable delays
2. **Compatibility**: Maintain existing output format `{"paths": [...], "layers": [...]}`
3. **Robustness**: Handle malformed input gracefully without crashing
4. **Maintainability**: Keep code readable and well-documented

## Success Criteria

1. Parser correctly handles modal state transitions across complex G-code programs
2. Arc processing works correctly for all valid I/J/K and R combinations
3. Program structure analysis provides useful feedback about missing initialization
4. Coordinate validation catches extreme values without false positives  
5. All existing tests continue to pass
6. New functionality is covered by comprehensive tests

## Technical Constraints

- Must maintain compatibility with existing `app/editor.py` and `app/preview.py`
- Cannot break existing diagnostic message format
- Should not significantly increase parsing time for typical files
- Must work with Python 3.11+ and current dependencies

## Context

This enhancement is inspired by robust G-code generation patterns found in the Gerber2nc project, particularly around modal state management, arc calculations, and program structure handling.
