# G-code Parser Enhancement Plan - v1.1 Compliance

## Executive Summary
Mevcut `app/gcode_parser.py` dosyasını v1.1 standardına tam uyumlu hale getirmek için detaylı plan. Mevcut parser temel G/M kodlarını desteklerken, endüstriyel standartlardaki birçok önemli komutu eksiktir.

## Current State Analysis

### ✅ Already Supported (17/35 codes)
**G Codes (11/25):**
- G0, G1: Linear Motions
- G2, G3: Arc and Helical Motions  
- G4: Dwell
- G17, G18, G19: Plane Selection
- G20, G21: Units
- G28: Go to Pre-Defined Position
- G54-G59: Work Coordinate Systems
- G90, G91: Distance Modes
- G94, G95: Feedrate Modes

**M Codes (6/10):**
- M0, M1, M2, M30: Program Pause and End
- M3, M4, M5: Spindle Control
- M6: Tool Change
- M7, M8, M9: Coolant Control

### ❌ Missing Critical Codes (18/35 codes)

**High Priority G Codes (8):**
- G10 L2/L20: Set Work Coordinate Offsets
- G53: Move in Absolute Coordinates
- G80: Motion Mode Cancel
- G92: Coordinate Offset
- G28.1, G30.1: Set Pre-Defined Position
- G30: Go to Pre-Defined Position (missing G30)
- G40: Cutter Radius Compensation OFF

**Medium Priority G Codes (6):**
- G38.2-G38.5: Probing commands
- G43.1, G49: Dynamic Tool Length Offsets
- G61: Path Control Modes
- G91.1: Arc IJK Distance Modes
- G92.1: Clear Coordinate System Offsets

**Low Priority M Codes (4):**
- M56: Parking Motion Override Control

## Implementation Strategy

### Phase 1: Core Industrial Commands (Week 1-2)
**Target: Add 8 high-priority G codes**

#### 1.1 G10 L2/L20 - Work Coordinate Offsets
```python
# ModalState additions:
self.work_offset = {"X": 0.0, "Y": 0.0, "Z": 0.0}  # G10 offsets
self.g10_active = False

# Parser logic:
elif gnum == 10:
    l_param = params.get("L")
    if l_param == 2:
        # Set work coordinate offsets
        for axis in ["X", "Y", "Z"]:
            if axis in params:
                modal_state.work_offset[axis] = params[axis]
        modal_state.g10_active = True
    elif l_param == 20:
        # Set work coordinate offsets (alternative)
        for axis in ["X", "Y", "Z"]:
            if axis in params:
                modal_state.work_offset[axis] = params[axis]
```

#### 1.2 G53 - Absolute Coordinate Movement
```python
# Parser logic:
elif gnum == 53:
    # Move in machine coordinates (ignore work offsets)
    path_obj = {
        "type": "absolute_move",
        "start": (x, y, z),
        "end": (new_x, new_y, new_z),
        "coordinate_system": "machine",  # Special flag
        "line_no": line_no,
        "line": original_line,
    }
    paths.append(path_obj)
```

#### 1.3 G80 - Motion Mode Cancel
```python
# ModalState additions:
self.motion_mode = None  # G80 cancels motion mode

# Parser logic:
elif gnum == 80:
    modal_state.motion = None  # Cancel motion mode
    paths.append({
        "type": "motion_cancel",
        "line_no": line_no,
        "line": original_line,
    })
```

#### 1.4 G92 - Coordinate Offset
```python
# ModalState additions:
self.coordinate_offset = {"X": 0.0, "Y": 0.0, "Z": 0.0}
self.g92_active = False

# Parser logic:
elif gnum == 92:
    # Set coordinate offset
    for axis in ["X", "Y", "Z"]:
        if axis in params:
            modal_state.coordinate_offset[axis] = params[axis]
    modal_state.g92_active = True
```

#### 1.5 G28.1/G30.1 - Set Pre-Defined Position
```python
# ModalState additions:
self.predefined_position = {"X": 0.0, "Y": 0.0, "Z": 0.0}

# Parser logic:
elif gnum == 28.1:
    # Set home position 1
    for axis in ["X", "Y", "Z"]:
        if axis in params:
            modal_state.predefined_position[axis] = params[axis]
elif gnum == 30.1:
    # Set home position 2
    for axis in ["X", "Y", "Z"]:
        if axis in params:
            modal_state.predefined_position[axis] = params[axis]
```

#### 1.6 G30 - Add Missing G30 Support
```python
# Parser logic:
elif gnum == 30:
    paths.append({
        "type": "home2",  # Second home position
        "start": (x, y, z),
        "line": original_line,
        "line_no": line_no,
    })
```

#### 1.7 G40 - Cutter Compensation OFF
```python
# ModalState additions:
self.cutter_compensation = "G40"  # Default OFF

# Parser logic:
elif gnum == 40:
    modal_state.cutter_compensation = "G40"
    paths.append({
        "type": "cutter_comp_off",
        "line_no": line_no,
        "line": original_line,
    })
```

### Phase 2: Advanced Features (Week 3-4)
**Target: Add 6 medium-priority codes**

#### 2.1 G38.x - Probing Commands
```python
# Parser logic:
elif gnum == 38.2:
    paths.append({
        "type": "probe_toward",
        "probe_signal": params.get("J", 0),
        "line_no": line_no,
        "line": original_line,
    })
elif gnum == 38.3:
    paths.append({
        "type": "probe_away",
        "probe_signal": params.get("J", 0),
        "line_no": line_no,
        "line": original_line,
    })
elif gnum == 38.4:
    paths.append({
        "type": "probe_toward_error",
        "probe_signal": params.get("J", 0),
        "line_no": line_no,
        "line": original_line,
    })
elif gnum == 38.5:
    paths.append({
        "type": "probe_away_error", 
        "probe_signal": params.get("J", 0),
        "line_no": line_no,
        "line": original_line,
    })
```

#### 2.2 G43.1/G49 - Tool Length Offsets
```python
# ModalState additions:
self.tool_length_offset = 0.0
self.tool_length_compensation = "G49"  # Default OFF

# Parser logic:
elif gnum == 43.1:
    modal_state.tool_length_compensation = "G43.1"
    if "H" in params:
        modal_state.tool_length_offset = params["H"]
elif gnum == 49:
    modal_state.tool_length_compensation = "G49"
    modal_state.tool_length_offset = 0.0
```

#### 2.3 G61 - Path Control Modes
```python
# ModalState additions:
self.path_control = "G61"  # Exact path control

# Parser logic:
elif gnum == 61:
    modal_state.path_control = "G61"
    paths.append({
        "type": "exact_path_control",
        "line_no": line_no,
        "line": original_line,
    })
```

#### 2.4 G91.1 - Arc IJK Distance Modes
```python
# ModalState additions:
self.arc_distance_mode = "G90"  # Default absolute IJK

# Parser logic:
elif gnum == 91.1:
    modal_state.arc_distance_mode = "G91.1"
    # Modify arc calculation to use incremental IJK
```

#### 2.5 G92.1 - Clear Coordinate Offsets
```python
# Parser logic:
elif gnum == 92.1:
    modal_state.coordinate_offset = {"X": 0.0, "Y": 0.0, "Z": 0.0}
    modal_state.g92_active = False
    paths.append({
        "type": "clear_coordinate_offset",
        "line_no": line_no,
        "line": original_line,
    })
```

### Phase 3: Specialized Features (Week 5-6)
**Target: Add remaining 4 low-priority codes**

#### 3.1 M56 - Parking Motion Override
```python
# Parser logic:
elif mnum == 56:
    paths.append({
        "type": "parking_override",
        "override_code": params.get("P", 0),
        "line_no": line_no,
        "line": original_line,
    })
```

## Technical Implementation Details

### 3.1 ModalState Class Enhancement
```python
class ModalState:
    def __init__(self):
        # Existing properties...
        
        # New properties for v1.1 compliance
        self.work_offset = {"X": 0.0, "Y": 0.0, "Z": 0.0}
        self.g10_active = False
        self.coordinate_offset = {"X": 0.0, "Y": 0.0, "Z": 0.0}
        self.g92_active = False
        self.predefined_position = {"X": 0.0, "Y": 0.0, "Z": 0.0}
        self.cutter_compensation = "G40"
        self.tool_length_offset = 0.0
        self.tool_length_compensation = "G49"
        self.path_control = "G61"
        self.arc_distance_mode = "G90"
        self.motion_mode = None  # G80 support
```

### 3.2 Enhanced Error Handling
```python
# New diagnostic messages
MESSAGES.update({
    "invalid_g10_l": "G10 requires L2 or L20 parameter",
    "invalid_probe": "G38.x requires probe signal parameter",
    "invalid_tool_length": "G43.1 requires H parameter",
    "coordinate_conflict": "G92 conflicts with G10 active",
})
```

### 3.3 Test Coverage Expansion
```python
# New test categories:
tests/contract/test_g10_work_offsets.py
tests/contract/test_g53_absolute_moves.py
tests/contract/test_g80_motion_cancel.py
tests/contract/test_g92_coordinate_offset.py
tests/contract/test_g38_probing.py
tests/contract/test_g43_tool_length.py
tests/contract/test_m56_parking.py
```

## Validation Strategy

### 4.1 Unit Tests
- Each new G/M code gets dedicated test file
- Modal state transitions tested
- Parameter validation tested
- Error conditions tested

### 4.2 Integration Tests
- Complex programs with mixed new/old commands
- Modal state persistence across command changes
- Backward compatibility verification

### 4.3 Performance Tests
- Large file parsing with new commands
- Memory usage validation
- Processing speed benchmarks

## Risk Assessment

### 5.1 Technical Risks
- **Modal State Complexity**: New modal groups may create conflicts
- **Backward Compatibility**: Existing tests may fail
- **Performance**: Additional validation may slow parsing

### 5.2 Mitigation Strategies
- Incremental implementation with feature flags
- Comprehensive test suite before each phase
- Performance profiling at each milestone

## Success Metrics

### 6.1 Compliance Metrics
- **Target**: 100% v1.1 G-code support (35/35 codes)
- **Current**: 49% support (17/35 codes)
- **Phase 1 Goal**: 71% support (25/35 codes)
- **Final Goal**: 100% support (35/35 codes)

### 6.2 Quality Metrics
- **Test Coverage**: >95% for new features
- **Performance**: <5% parsing speed degradation
- **Compatibility**: 100% backward compatibility

## Timeline

| Phase | Duration | Target Codes | Success Criteria |
|--------|----------|---------------|------------------|
| Phase 1 | Week 1-2 | 8 high-priority G codes | Core industrial functionality |
| Phase 2 | Week 3-4 | 6 medium-priority codes | Advanced features |
| Phase 3 | Week 5-6 | 4 low-priority codes | Complete v1.1 compliance |
| Testing | Week 7-8 | Comprehensive validation | Production ready |

## Resource Requirements

### 7.1 Development Resources
- **Lead Developer**: 1 FTE for 6 weeks
- **QA Engineer**: 0.5 FTE for test development
- **Code Review**: 2 hours per phase

### 7.2 Infrastructure
- **Test Environment**: Enhanced test data sets
- **CI/CD**: Additional test pipelines
- **Documentation**: Updated API docs

## Conclusion

Bu plan, mevcut G-code parser'ı endüstriyel v1.1 standardına tam uyumlu hale getirmek için yapılandırılmıştır. 3 fazda 18 yeni G/M kodu ekleyerek %51'den %100 destek seviyesine ulaşmayı hedefler. Her faz risk değerlendirmesi ve kalite metrikleri ile desteklenmektedir.

Planın başarısı, CNC endüstrisindeki yaygın kullanım senaryolarını kapsayarak parser'ın endüstriyel kullanım için hazır hale gelmesini sağlayacaktır.

## Next Steps

1. **Immediate Actions (Week 1):**
   - Create feature branch for v1.1 enhancement
   - Implement ModalState enhancements
   - Add G10 L2/L20 support with tests

2. **Phase 1 Implementation (Week 1-2):**
   - Complete all 8 high-priority G codes
   - Ensure backward compatibility
   - Update documentation

3. **Validation & Review:**
   - Run existing test suite
   - Performance benchmarking
   - Code review and integration

4. **Subsequent Phases:**
   - Follow timeline for Phase 2 and 3
   - Continuous integration testing
   - Production deployment preparation

---

**Document Version:** 1.0  
**Created:** November 26, 2025  
**Status:** Ready for Implementation  
**Next Review:** End of Phase 1 (Week 2)