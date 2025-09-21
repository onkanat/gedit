# Parser Contract: Enhanced G-code Parser

## Function Signature

```python
def parse_gcode(code: str) -> dict:
    """
    Enhanced G-code parser with modal state management, coordinate validation, 
    and improved arc processing.
    
    Args:
        code (str): G-code text to parse
        
    Returns:
        dict: Parser result with structure:
            {
                "paths": List[dict],     # Path entries (movements and diagnostics)
                "layers": List[dict]     # Layer information
            }
    """
```

## Input Contract

### Requirements
- `code` must be a string (may be empty)
- Lines may contain G-code commands, comments, or be empty
- Comments start with `;` and extend to end of line
- Commands are case-insensitive but output uses uppercase
- Numeric values may be integers or floats

### Supported Commands

**G-codes:**
- G0: Rapid positioning
- G1: Linear interpolation 
- G2: Circular interpolation (clockwise)
- G3: Circular interpolation (counterclockwise)
- G4: Dwell
- G17: XY plane selection
- G18: XZ plane selection  
- G19: YZ plane selection
- G20: Inch units
- G21: Millimeter units
- G28: Return to home
- G54-G59: Coordinate system selection
- G90: Absolute positioning
- G91: Incremental positioning
- G94: Feed rate mode (units per minute)

**M-codes:**
- M0, M1: Program pause
- M2: Program end
- M3: Spindle on clockwise
- M4: Spindle on counterclockwise  
- M5: Spindle stop
- M6: Tool change
- M7: Mist coolant on
- M8: Flood coolant on
- M9: Coolant off
- M30: Program end and rewind

**Parameters:**
- X, Y, Z: Axis coordinates
- I, J, K: Arc center offsets
- R: Arc radius
- F: Feed rate
- S: Spindle speed
- P: Dwell time

## Output Contract

### Structure Guarantee
```python
{
    "paths": List[dict],    # Always present, may be empty
    "layers": List[dict]    # Always present, may be empty
}
```

### Path Entry Types

**Movement Entries ("rapid", "feed", "arc"):**
```python
{
    "type": str,                    # "rapid", "feed", "arc"
    "start": Tuple[float, float, float],  # Start coordinates (X, Y, Z)
    "end": Tuple[float, float, float],    # End coordinates (X, Y, Z)
    "line_no": int,                 # Source line number (1-based)
    "line": str,                    # Original line content
    "feed_rate": Optional[float],   # Feed rate if specified
    "plane": str,                   # Work plane ("G17", "G18", "G19")
    "coord_system": str,            # Coordinate system ("G54"-"G59")
    "layer": Optional[int],         # Layer number if in layer
    
    # Arc-specific fields:
    "direction": str,               # "clockwise", "counter_clockwise" (arc only)
    
    # NEW OPTIONAL FIELDS:
    "modal_state": Optional[dict],  # Modal state snapshot
    "validation": Optional[dict],   # Validation results
    "program_structure": Optional[str], # "header", "footer", "body"
}
```

**Diagnostic Entries ("parse_error", "unsupported", "unknown_param", "warning"):**
```python
{
    "type": str,           # Diagnostic type
    "message": str,        # Error/warning message  
    "line_no": int,        # Source line number
    "line": str,           # Original line content
    
    # Type-specific fields:
    "code": Optional[str],      # Command code (for unsupported)
    "word": Optional[str],      # Problem word (for parse_error)
    "param": Optional[str],     # Parameter letter (for unknown_param)
    "coordinate": Optional[str], # Axis name (for coordinate warnings)
    "value": Optional[float],   # Problematic value
}
```

### Layer Entries
```python
{
    "layer": int,              # Layer number from ;LAYER: comment
    "paths": Optional[List[int]] # Indices into paths array (if tracking enabled)
}
```

## Behavioral Contract

### Modal State Management
- Parser maintains modal state across lines
- Default modal state: G0 G17 G21 G90 G94 G54
- Modal state changes persist until explicitly changed
- M30/M2 commands reset modal state to defaults
- Position tracking includes absolute/incremental mode handling

### Arc Processing
- R parameter takes precedence over I/J/K when both present
- I/J/K values are offsets from start position to arc center
- Arc parameters validated against current work plane:
  - G17 (XY): Requires I and/or J
  - G18 (XZ): Requires I and/or K  
  - G19 (YZ): Requires J and/or K
- Invalid arc definitions generate "parse_error" diagnostics

### Coordinate Validation
- Large coordinate values (>1000mm default) generate warnings
- Validation considers current units (G20/G21)
- Warnings are non-blocking (parsing continues)

### Program Structure Analysis  
- First 10 lines scanned for initialization patterns
- Last 5 lines scanned for termination commands
- Missing structure generates warnings, not errors
- Structure information available in path entries

### Error Handling
- Invalid syntax generates "parse_error" entries
- Unsupported commands generate "unsupported" entries  
- Unknown parameters generate "unknown_param" entries
- Coordinate warnings generate "warning" entries
- Parser continues processing after errors when possible

### Backward Compatibility
- All existing path entry fields maintained
- New fields are optional and may be None/missing
- Output structure unchanged: `{"paths": [...], "layers": [...]}`
- Existing diagnostic message formats preserved

## Performance Contract

- Handle files up to 100K lines in <1 second on modern hardware
- Memory usage scales linearly with input size
- No external dependencies beyond Python standard library

## Test Requirements

### Unit Tests Required
- Modal state initialization and transitions
- Arc parameter validation for all work planes  
- Coordinate validation with different units
- Program structure detection patterns
- Error message generation and formatting
- Backward compatibility with existing output format

### Integration Tests Required
- Parse real-world G-code files (CAM output)
- Verify modal state persistence across complex programs
- Validate arc processing with mixed R and I/J/K parameters
- Confirm coordinate warnings at appropriate thresholds
- Test program structure analysis on various file types

### Contract Validation
- All path entries have required fields
- Diagnostic entries include proper error messages
- Layer information correctly extracted from comments  
- Modal state changes properly tracked and applied
- Arc geometry calculations produce valid results
