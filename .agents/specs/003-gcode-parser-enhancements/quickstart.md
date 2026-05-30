# Quickstart: G-code Parser Enhancements

## Overview

Quick validation and testing guide for the enhanced G-code parser functionality.

## Development Setup

1. **Environment Requirements**
   - Python 3.11+ 
   - pytest for testing
   - Existing project dependencies (matplotlib, numpy)

2. **Files to Modify**
   - `app/gcode_parser.py` - Main parser implementation
   - `tests/test_gcode_parser.py` - Existing test file
   - Create new test files for enhanced functionality

## Quick Validation Steps

### 1. Modal State Management Test

**Input G-code:**
```gcode
G17 G21 G90 G94
G0 X10 Y10
G1 X20 Y20
G2 X30 Y10 I5 J0
M30
G0 X0 Y0
```

**Expected Behavior:**
- First G0 should use modal state from initialization (G17, G21, G90, G94)
- Arc G2 should use I/J parameters (valid for G17 plane)
- After M30, modal state should reset
- Final G0 should use reset modal state

**Test Command:**
```python
python3 -c "
from app.gcode_parser import parse_gcode
result = parse_gcode(open('test_modal.nc').read())
print(f'Total paths: {len(result[\"paths\"])}')
for i, path in enumerate(result['paths']):
    modal = path.get('modal_state', {})
    print(f'Path {i}: type={path.get(\"type\")}, plane={modal.get(\"plane\")}, units={modal.get(\"units\")}')
"
```

### 2. Arc Processing Test

**Input G-code:**
```gcode
G17 G21 G90
G0 X0 Y0
G2 X10 Y0 R5
G3 X20 Y0 I5 J0
G2 X30 Y0 I5 J0 R5
```

**Expected Behavior:**
- First arc uses R parameter (should work)
- Second arc uses I/J parameters (should work for G17 plane)
- Third arc has both R and I/J (R should take precedence)
- All arcs should generate valid movement paths

**Test Command:**
```python
python -c "
from app.gcode_parser import parse_gcode
result = parse_gcode(open('test_arcs.nc').read())
arc_paths = [p for p in result['paths'] if p.get('type') == 'arc']
print(f'Arc paths: {len(arc_paths)}')
print(f'Arc errors: {sum(1 for p in result[\"paths\"] if p.get(\"type\") == \"parse_error\" and \"arc\" in p.get(\"message\", \"\").lower())}')
"
```

### 3. Coordinate Validation Test

**Input G-code:**
```gcode
G21 G90
G0 X10 Y10
G1 X2000 Y2000
G0 X-1500 Y0
```

**Expected Behavior:**
- Normal coordinates (X10 Y10) should not generate warnings
- Large coordinates (X2000 Y2000) should generate warnings
- Negative large coordinate (-1500) should generate warning
- Movement should still be parsed successfully

**Test Command:**
```python
python -c "
from app.gcode_parser import parse_gcode
result = parse_gcode(open('test_coords.nc').read())
warnings = [p for p in result['paths'] if p.get('type') == 'warning']
print(f'Coordinate warnings: {len(warnings)}')
for w in warnings:
    print(f'  {w.get(\"message\")}')
"
```

### 4. Program Structure Test

**Input G-code with header:**
```gcode
; Program start
G17 G21 G90 G94
M3 S1000
G0 X0 Y0
G1 X10 Y10 F100
M5
M30
```

**Input G-code without header:**
```gcode
G0 X0 Y0
G1 X10 Y10
```

**Expected Behavior:**
- First program should be recognized as having proper structure
- Second program should generate structure warnings
- Both should parse successfully

**Test Command:**
```python
python -c "
from app.gcode_parser import parse_gcode
result1 = parse_gcode(open('test_with_header.nc').read())
result2 = parse_gcode(open('test_no_header.nc').read())
struct_warnings1 = [p for p in result1['paths'] if 'header' in p.get('message', '').lower()]
struct_warnings2 = [p for p in result2['paths'] if 'header' in p.get('message', '').lower()]
print(f'Header warnings - with header: {len(struct_warnings1)}, without header: {len(struct_warnings2)}')
"
```

## Integration Testing

### With Preview System

**Test that enhanced parser output works with existing preview:**

```python
from app.gcode_parser import parse_gcode
from app.preview import PreviewWindow
import tkinter as tk

# Test G-code with enhancements
test_code = '''
G17 G21 G90 G94
G0 X0 Y0 Z5
G1 Z0 F100
G2 X10 Y0 I5 J0 F200
G0 Z5
M30
'''

root = tk.Tk()
result = parse_gcode(test_code)
preview = PreviewWindow(root)
preview.update_preview(result)
root.mainloop()
```

**Expected Result:**
- Preview should display correctly
- No errors in console
- Enhanced paths should render properly
- Modal state changes should not break visualization

### With Editor System

**Test that enhanced diagnostics work with editor:**

```python
from app.gcode_parser import parse_gcode
from app.editor import Editor
import tkinter as tk

# Test G-code with errors
test_code = '''
G17 G21 G90
G2 X10 Y0
G1 X2000 Y2000
'''

root = tk.Tk()
editor = Editor(root)
editor.set_text(test_code)
result = parse_gcode(test_code)
editor.update_diagnostics(result)
# Should see error highlighting for invalid arc and coordinate warnings
```

**Expected Result:**
- Invalid arc should be highlighted as error
- Large coordinates should be highlighted as warnings  
- Line numbers should be correct
- Editor should remain responsive

## Performance Validation

### Large File Test

**Generate large test file:**

```python
# Generate 50K line test file
with open('large_test.nc', 'w') as f:
    f.write('G17 G21 G90 G94\n')
    for i in range(50000):
        f.write(f'G1 X{i*0.1} Y{(i*0.1)%100}\n')
    f.write('M30\n')
```

**Performance Test:**

```python
import time
from app.gcode_parser import parse_gcode

start = time.time()
with open('large_test.nc', 'r') as f:
    result = parse_gcode(f.read())
end = time.time()

print(f'Parsed {len(result["paths"])} paths in {end-start:.2f} seconds')
print(f'Performance: {len(result["paths"])/(end-start):.0f} paths/second')
```

**Expected Result:**
- Should complete in under 1 second
- Should generate 50K+ path entries
- Memory usage should be reasonable (<100MB)

## Regression Testing

### Existing Functionality

**Run all existing tests:**
```bash
cd /Users/hakankilicaslan/Git/gedit
python -m pytest tests/test_gcode_parser.py -v
```

**Expected Result:**
- All existing tests should pass
- No changes to existing test behavior
- Backward compatibility maintained

### Example Files

**Test with existing example files:**
```python
from app.gcode_parser import parse_gcode

# Test with existing examples
for filename in ['DENEME.nc', 'deneme02.nc', 'EXAMPLE_POCKET.nc']:
    with open(filename, 'r') as f:
        result = parse_gcode(f.read())
        print(f'{filename}: {len(result["paths"])} paths, {len(result["layers"])} layers')
```

**Expected Result:**
- Should parse without errors
- Path counts should be same or higher (due to enhanced detection)
- Layer detection should work as before

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure you're in the project root directory
   - Check Python path includes the project directory

2. **Test File Creation**
   - Create test files in project root or specify full paths
   - Ensure proper line endings (Unix style preferred)

3. **Performance Issues**
   - Check for infinite loops in modal state management
   - Verify coordinate validation doesn't have expensive operations

4. **Preview Integration**
   - Enhanced fields are optional - preview should ignore them
   - Check for None values in new fields before using

### Debug Mode

**Enable detailed output:**
```python
from app.gcode_parser import parse_gcode

# Add debug parameter (if implemented)
result = parse_gcode(code, debug=True)
```

## Success Criteria Validation

After running all quickstart tests, verify:

- [ ] Modal state management works correctly
- [ ] Arc processing handles all parameter combinations
- [ ] Coordinate validation generates appropriate warnings
- [ ] Program structure detection works on various files
- [ ] Existing functionality remains unchanged
- [ ] Performance meets requirements (<1 second for 100K lines)
- [ ] Integration with preview and editor works
- [ ] All existing tests pass
