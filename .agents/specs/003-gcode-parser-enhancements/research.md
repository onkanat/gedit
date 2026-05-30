# Research: G-code Parser Enhancements

## Overview

Research findings for enhancing the G-code parser based on patterns found in the Gerber2nc project and analysis of current parser limitations.

## Key Research Areas

### 1. Modal State Management

**Decision**: Implement comprehensive modal state tracking with proper initialization and reset behaviors

**Rationale**: 
- Current parser has basic modal tracking but lacks proper initialization and reset logic
- Gerber2nc shows clear patterns for modal state management in G-code generation
- Real-world G-code files rely heavily on modal commands staying active until explicitly changed
- Program structure (header/footer) affects modal state expectations

**Alternatives considered**:
- Stateless parsing: Rejected due to G-code's inherent modal nature
- Partial modal tracking: Current approach is insufficient for complex files

**Implementation approach**:
- Initialize modal states with industry-standard defaults (G0, G17, G21, G90, G94, G54)
- Reset states on program end commands (M30, M2) 
- Track additional modal states: distance mode, coordinate system, spindle state
- Validate modal state transitions

### 2. Arc Processing Improvements

**Decision**: Enhance arc processing with proper I/J/K center calculations and R parameter prioritization

**Rationale**:
- Current parser has incomplete arc validation leading to preview errors
- Gerber2nc demonstrates correct I/J/K calculation: center = start + offset
- R parameter should take precedence over I/J/K when both are present
- Different work planes (G17/G18/G19) require different I/J/K combinations

**Alternatives considered**:
- Simple R-only processing: Insufficient for complex toolpaths
- Keep current approach: Results in parsing failures and incorrect previews

**Implementation approach**:
- Calculate arc centers from I/J/K offsets relative to start position
- Validate I/J/K parameters match current work plane
- Prioritize R parameter when both R and I/J/K are present
- Provide clear error messages for invalid arc definitions

### 3. Program Structure Detection

**Decision**: Implement program structure analysis to detect initialization and termination patterns

**Rationale**:
- Many CAM systems generate predictable program structures
- Gerber2nc shows typical initialization sequence: G17 G21 G90 G94
- Missing initialization can cause modal state confusion
- Program termination affects modal state reset

**Alternatives considered**:
- Ignore program structure: Misses opportunity for better validation
- Strict structure enforcement: Too rigid for diverse G-code sources

**Implementation approach**:
- Scan first 10 lines for common initialization patterns
- Scan last 5 lines for termination commands
- Flag programs missing proper structure as warnings, not errors
- Use structure information to improve modal state management

### 4. Coordinate Validation

**Decision**: Add coordinate range validation with configurable limits

**Rationale**:
- Large coordinate values often indicate errors in G-code generation or units
- Gerber2nc includes safety checks for coordinate ranges
- Early detection prevents downstream issues in preview/simulation

**Alternatives considered**:
- No validation: Misses opportunity to catch errors early
- Fixed limits: Different applications have different valid ranges
- Post-processing validation: Too late to provide useful feedback

**Implementation approach**:
- Default maximum coordinate: 1000mm (configurable)
- Generate warnings (not errors) for extreme values
- Include coordinate name and value in diagnostic message
- Consider coordinate system and units when validating

### 5. Enhanced Error Reporting

**Decision**: Improve diagnostic messages with more context and suggestions

**Rationale**:
- Current error messages are minimal and don't provide enough context
- Users need guidance on how to fix common issues
- Maintaining backward compatibility is essential for existing integrations

**Alternatives considered**:
- Complete message system overhaul: Risk breaking existing code
- Minimal improvements: Insufficient for user experience improvement

**Implementation approach**:
- Extend diagnostic message templates with more context
- Include line numbers and original line content in all diagnostics
- Add suggestions for common error patterns
- Maintain existing diagnostic structure for compatibility

## Technical Research

### G-code Standards Reference

- **RS274NGC**: Industry standard for G-code interpretation
- **ISO 6983**: International standard for numerical control programming
- **LinuxCNC Documentation**: Comprehensive modal state reference

### Modal State Best Practices

From industry sources and LinuxCNC documentation:
- G0 (rapid motion) is typical default motion mode
- G17 (XY plane) is standard default work plane  
- G21 (millimeter) is common default units
- G90 (absolute positioning) is standard default
- G94 (units per minute feed rate) is typical default
- G54 (first coordinate system) is standard default

### Arc Processing Standards

- I/J/K values are offsets from start point to arc center
- R parameter specifies radius directly
- When both R and I/J/K are present, R takes precedence
- Work plane determines which I/J/K parameters are valid:
  - G17 (XY plane): I and J valid
  - G18 (XZ plane): I and K valid  
  - G19 (YZ plane): J and K valid

### Error Patterns Analysis

Common G-code parsing errors from community feedback:
1. Missing arc parameters (no R or appropriate I/J/K)
2. Incorrect work plane for arc definition
3. Extreme coordinate values due to unit confusion
4. Modal state confusion in complex programs
5. Missing program initialization causing downstream errors

## Conclusion

The research confirms that all five enhancement areas are valuable and feasible. The implementation should focus on:

1. Robust modal state management as the foundation
2. Improved arc processing for better preview accuracy
3. Program structure detection for better validation
4. Coordinate validation for early error detection  
5. Enhanced error messages for better user experience

All enhancements can be implemented while maintaining backward compatibility with the existing `{"paths": [...], "layers": [...]}` output format.
