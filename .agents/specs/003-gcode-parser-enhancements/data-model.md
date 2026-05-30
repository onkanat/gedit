# Data Model: G-code Parser Enhancements

## Overview

Data model changes and extensions for the enhanced G-code parser, maintaining backward compatibility while adding new capabilities.

## Core Entities

### ParseResult (Root Output)

**Current Structure** (maintained for compatibility):
```python
{
    "paths": List[PathEntry],
    "layers": List[LayerInfo]
}
```

**Fields**:
- `paths`: List of path entries (movements, diagnostics)
- `layers`: List of layer information from ;LAYER comments

### PathEntry (Enhanced)

**Current Structure** (extended):
```python
{
    # Existing fields (maintained):
    "type": str,           # "rapid", "feed", "arc", "parse_error", "unsupported", "unknown_param"
    "line_no": int,        # Line number in source
    "line": str,           # Original line content
    
    # For movement types ("rapid", "feed", "arc"):
    "start": Tuple[float, float, float],  # Start coordinates
    "end": Tuple[float, float, float],    # End coordinates
    
    # For arc types only:
    "direction": str,      # "clockwise", "counter_clockwise"
    
    # For diagnostic types:
    "message": str,        # Error/warning message
    
    # NEW FIELDS:
    "modal_state": Optional[ModalState],  # Snapshot of modal state
    "validation": Optional[ValidationResult],  # Coordinate/parameter validation
    "program_structure": Optional[str],  # "header", "footer", "body"
}
```

**Validation Rules**:
- `type` must be one of defined types
- Movement entries must have valid `start` and `end` coordinates
- Diagnostic entries must have `message`
- Arc entries must have valid `direction`

**State Transitions**:
- Paths are processed sequentially
- Each path may update modal state for subsequent paths
- Diagnostic paths do not affect movement state

### ModalState (New Entity)

**Structure**:
```python
{
    "motion": str,         # Current motion mode: "G0", "G1", "G2", "G3"
    "plane": str,          # Work plane: "G17", "G18", "G19"
    "units": str,          # Units: "G20" (inches), "G21" (mm)
    "distance": str,       # Distance mode: "G90" (absolute), "G91" (incremental)
    "feed_mode": str,      # Feed mode: "G94" (units/minute)
    "coord_system": str,   # Coordinate system: "G54", "G55", "G56", "G57", "G58", "G59"
    "spindle": Optional[SpindleState],  # Spindle state
    "coolant": Optional[CoolantState],  # Coolant state
}
```

**Default Values**:
- `motion`: "G0"
- `plane`: "G17"
- `units`: "G21"
- `distance`: "G90"
- `feed_mode`: "G94"
- `coord_system`: "G54"
- `spindle`: None
- `coolant`: None

**State Transitions**:
- States persist until explicitly changed by G/M commands
- Program end (M30, M2) resets states to defaults
- Invalid state transitions generate diagnostics

### SpindleState (New Entity)

**Structure**:
```python
{
    "state": str,          # "on_cw", "on_ccw", "off"
    "speed": Optional[int], # RPM if specified
    "command": str,        # Original M command: "M3", "M4", "M5"
}
```

**Validation Rules**:
- `state` must be one of defined values
- `speed` must be positive integer when present
- State changes logged in diagnostics

### CoolantState (New Entity)

**Structure**:
```python
{
    "mist": bool,          # M7 mist coolant
    "flood": bool,         # M8 flood coolant
    "commands": List[str], # Commands that set this state
}
```

**Default Values**:
- `mist`: False
- `flood`: False
- `commands`: []

### ValidationResult (New Entity)

**Structure**:
```python
{
    "coordinate_warnings": List[CoordinateWarning],
    "parameter_warnings": List[ParameterWarning],
    "arc_validation": Optional[ArcValidation],
}
```

### CoordinateWarning (New Entity)

**Structure**:
```python
{
    "axis": str,           # "X", "Y", "Z"
    "value": float,        # Coordinate value
    "threshold": float,    # Maximum allowed value
    "message": str,        # Warning message
}
```

### ParameterWarning (New Entity)

**Structure**:
```python
{
    "parameter": str,      # Parameter letter
    "value": str,          # Raw parameter value
    "expected_type": str,  # "numeric", "integer"
    "message": str,        # Warning message
}
```

### ArcValidation (New Entity)

**Structure**:
```python
{
    "has_radius": bool,    # R parameter present
    "has_center": bool,    # I/J/K parameters present
    "radius_value": Optional[float],    # R parameter value
    "center_offset": Optional[Tuple[float, float, float]],  # I, J, K values
    "calculated_radius": Optional[float],  # Calculated from I/J/K
    "plane_compatible": bool,  # Parameters match work plane
    "valid": bool,         # Overall validation result
    "errors": List[str],   # Validation error messages
}
```

### LayerInfo (Unchanged)

**Structure** (maintained for compatibility):
```python
{
    "layer": int,          # Layer number from ;LAYER comment
    "paths": List[int],    # Indices into paths array (optional)
}
```

## Parser State Management

### ParserContext (Internal State)

**Structure**:
```python
{
    "position": Tuple[float, float, float],  # Current X, Y, Z
    "previous_position": Tuple[float, float, float],  # Previous X, Y, Z
    "modal_state": ModalState,  # Current modal state
    "unit_scale": float,       # Scaling factor (1.0 for mm, 25.4 for inches)
    "absolute_mode": bool,     # True for G90, False for G91
    "current_layer": Optional[int],  # Current layer from ;LAYER comment
    "line_number": int,        # Current line being parsed
    "program_structure": ProgramStructure,  # Program analysis
}
```

### ProgramStructure (New Entity)

**Structure**:
```python
{
    "has_header": bool,          # Detected initialization sequence
    "has_footer": bool,          # Detected termination sequence
    "header_lines": List[int],   # Line numbers of header commands
    "footer_lines": List[int],   # Line numbers of footer commands
    "initialization_commands": List[str],  # Commands found in header
    "termination_commands": List[str],     # Commands found in footer
}
```

## Diagnostic Message Templates

### Enhanced Messages (Extended)

**Current Messages** (maintained):
```python
MESSAGES = {
    'unsupported_g': "Unsupported G-code {code}",
    'unsupported_m': "Unsupported M-code {code}",
    'unknown_param': "Unknown parameter letter '{letter}' in '{word}'",
    'invalid_numeric': "Invalid numeric value for '{letter}': '{bad}'",
    'invalid_word': "Invalid word format: '{word}'",
    'invalid_layer_comment': 'Invalid layer comment format',
    'arc_requirements': 'Arc (G2/G3) requires R>0 or appropriate I/J/K values (per plane).',
    
    # NEW MESSAGES:
    'coordinate_warning': "Large {axis} coordinate: {value} (threshold: {threshold})",
    'modal_state_reset': "Modal states reset by {command}",
    'arc_center_mismatch': "Arc center calculation mismatch: R={radius}, calculated={calc}",
    'plane_parameter_mismatch': "Parameter {param} not valid for work plane {plane}",
    'program_missing_header': "Program missing initialization sequence (G17 G21 G90 G94)",
    'program_missing_footer': "Program missing termination command (M30 or M2)",
    'spindle_speed_warning': "Spindle speed {speed} may be excessive",
}
```

## Relationships

### Parser Flow

1. **Initialize** → Create ParserContext with default ModalState
2. **Analyze Structure** → Scan for header/footer patterns
3. **Parse Lines** → Process each line, updating context
4. **Generate Paths** → Create PathEntry objects with validation
5. **Return Result** → Package as ParseResult

### Data Flow

```
Input G-code → ParserContext → PathEntry[] → ParseResult
              ↓
           ModalState → ValidationResult
              ↓
         ProgramStructure
```

## Backward Compatibility

### Guaranteed Fields

All existing consumers can expect these fields to remain unchanged:
- `paths[].type`
- `paths[].line_no`
- `paths[].line`
- `paths[].start` (for movements)
- `paths[].end` (for movements)
- `paths[].message` (for diagnostics)
- `layers[].layer`

### New Optional Fields

All new fields are optional and can be safely ignored by existing consumers:
- `paths[].modal_state`
- `paths[].validation`
- `paths[].program_structure`

### Migration Strategy

Existing code will continue to work without changes. New features can opt in to enhanced data by checking for presence of new fields.
