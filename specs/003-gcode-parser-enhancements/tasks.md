# Tasks: G-code Parser Enhancements

**Input**: Design documents from `/Users/hakankilicaslan/Git/gedit/specs/003-gcode-parser-enhancements/`
**Prerequisites**: plan.md (✓), research.md (✓), data-model.md (✓), contracts/ (✓)

## Execution Flow (main)
```
1. Load plan.md from feature directory ✓
   → Tech stack: Python 3.11+, pytest, existing dependencies
   → Structure: Single project - enhancing existing parser library
2. Load design documents: ✓
   → data-model.md: ModalState, ValidationResult, ArcValidation, etc.
   → contracts/parser.md: Enhanced parse_gcode function contract
   → research.md: 5 key enhancement areas identified
3. Generate tasks by category:
   → Setup: No new dependencies, linting with existing tools
   → Tests: Contract tests for enhanced parser functionality
   → Core: Modal state, arc processing, validation, error reporting
   → Integration: Parser integration with existing editor/preview
   → Polish: Performance tests, backward compatibility, docs
4. Apply task rules:
   → Different test files = mark [P] for parallel execution
   → Parser implementation = sequential (single file)
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001, T002...)
6. Dependencies: Modal state foundational, others can be parallel
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Single project**: Existing structure with `/Users/hakankilicaslan/Git/gedit/app/gcode_parser.py`
- **Tests**: `/Users/hakankilicaslan/Git/gedit/tests/` directory

## Phase 3.1: Setup
- [ ] T001 Review existing parser structure and create enhancement plan
- [ ] T002 Set up new test files for enhanced parser functionality  
- [ ] T003 [P] Create test data files for validation scenarios

## Phase 3.2: Contract Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Modal State Management Tests [P]
- [ ] T004 [P] Contract test: Modal state initialization with defaults in `/Users/hakankilicaslan/Git/gedit/tests/contract/test_modal_state_init.py`
- [ ] T005 [P] Contract test: Modal state persistence across lines in `/Users/hakankilicaslan/Git/gedit/tests/contract/test_modal_state_persistence.py`
- [ ] T006 [P] Contract test: Modal state reset on M30/M2 in `/Users/hakankilicaslan/Git/gedit/tests/contract/test_modal_state_reset.py`

### Arc Processing Tests [P]
- [ ] T007 [P] Contract test: R parameter precedence over I/J/K in `/Users/hakankilicaslan/Git/gedit/tests/contract/test_arc_r_precedence.py`
- [ ] T008 [P] Contract test: Arc center calculation from I/J/K offsets in `/Users/hakankilicaslan/Git/gedit/tests/contract/test_arc_ijk_calculation.py`
- [ ] T009 [P] Contract test: Work plane validation for arc parameters in `/Users/hakankilicaslan/Git/gedit/tests/contract/test_arc_plane_validation.py`

### Coordinate Validation Tests [P]
- [ ] T010 [P] Contract test: Large coordinate warnings in `/Users/hakankilicaslan/Git/gedit/tests/contract/test_coordinate_warnings.py`
- [ ] T011 [P] Contract test: Units-aware validation in `/Users/hakankilicaslan/Git/gedit/tests/contract/test_units_validation.py`

### Program Structure Tests [P]
- [ ] T012 [P] Contract test: Header pattern detection in `/Users/hakankilicaslan/Git/gedit/tests/contract/test_header_detection.py`
- [ ] T013 [P] Contract test: Footer pattern detection in `/Users/hakankilicaslan/Git/gedit/tests/contract/test_footer_detection.py`

### Enhanced Error Reporting Tests [P]
- [ ] T014 [P] Contract test: Enhanced diagnostic messages in `/Users/hakankilicaslan/Git/gedit/tests/contract/test_enhanced_diagnostics.py`
- [ ] T015 [P] Contract test: Context-rich error messages in `/Users/hakankilicaslan/Git/gedit/tests/contract/test_context_rich_errors.py`

## Phase 3.3: Core Implementation (ONLY after tests are failing)

### Foundation: Modal State Management
- [ ] T016 Implement ModalState data structure in `/Users/hakankilicaslan/Git/gedit/app/gcode_parser.py`
- [ ] T017 Implement modal state initialization and defaults in `/Users/hakankilicaslan/Git/gedit/app/gcode_parser.py`
- [ ] T018 Implement modal state tracking and persistence in `/Users/hakankilicaslan/Git/gedit/app/gcode_parser.py`
- [ ] T019 Implement modal state reset logic for M30/M2 in `/Users/hakankilicaslan/Git/gedit/app/gcode_parser.py`

### Arc Processing Enhancement
- [ ] T020 Implement enhanced arc parameter validation in `/Users/hakankilicaslan/Git/gedit/app/gcode_parser.py`
- [ ] T021 Implement R parameter precedence logic in `/Users/hakankilicaslan/Git/gedit/app/gcode_parser.py`
- [ ] T022 Implement I/J/K center calculation from offsets in `/Users/hakankilicaslan/Git/gedit/app/gcode_parser.py`
- [ ] T023 Implement work plane compatibility checking in `/Users/hakankilicaslan/Git/gedit/app/gcode_parser.py`

### Coordinate Validation System
- [ ] T024 Implement ValidationResult data structure in `/Users/hakankilicaslan/Git/gedit/app/gcode_parser.py`
- [ ] T025 Implement coordinate range validation in `/Users/hakankilicaslan/Git/gedit/app/gcode_parser.py`
- [ ] T026 Implement units-aware coordinate checking in `/Users/hakankilicaslan/Git/gedit/app/gcode_parser.py`

### Program Structure Detection  
- [ ] T027 Implement ProgramStructure analysis in `/Users/hakankilicaslan/Git/gedit/app/gcode_parser.py`
- [ ] T028 Implement header/footer pattern detection in `/Users/hakankilicaslan/Git/gedit/app/gcode_parser.py`

### Enhanced Error Reporting
- [ ] T029 Implement enhanced diagnostic message templates in `/Users/hakankilicaslan/Git/gedit/app/gcode_parser.py`
- [ ] T030 Implement context-rich error message generation in `/Users/hakankilicaslan/Git/gedit/app/gcode_parser.py`

## Phase 3.4: Integration Tests
- [ ] T031 [P] Integration test: Complex modal state scenarios in `/Users/hakankilicaslan/Git/gedit/tests/integration/test_complex_modal_scenarios.py`
- [ ] T032 [P] Integration test: Mixed arc parameter scenarios in `/Users/hakankilicaslan/Git/gedit/tests/integration/test_mixed_arc_scenarios.py`
- [ ] T033 [P] Integration test: Real-world CAM output parsing in `/Users/hakankilicaslan/Git/gedit/tests/integration/test_cam_output_parsing.py`
- [ ] T034 [P] Integration test: Large coordinate range validation in `/Users/hakankilicaslan/Git/gedit/tests/integration/test_large_coordinate_validation.py`
- [ ] T035 [P] Integration test: Program structure detection on various files in `/Users/hakankilicaslan/Git/gedit/tests/integration/test_program_structure_detection.py`

## Phase 3.5: System Integration
- [ ] T036 Integration test: Enhanced parser with existing editor in `/Users/hakankilicaslan/Git/gedit/tests/integration/test_parser_editor_integration.py`
- [ ] T037 Integration test: Enhanced parser with existing preview in `/Users/hakankilicaslan/Git/gedit/tests/integration/test_parser_preview_integration.py`
- [ ] T038 Integration test: Backward compatibility with existing example files in `/Users/hakankilicaslan/Git/gedit/tests/integration/test_backward_compatibility.py`

## Phase 3.6: Performance & Polish
- [ ] T039 [P] Performance test: 100K line parsing under 1 second in `/Users/hakankilicaslan/Git/gedit/tests/performance/test_large_file_performance.py`
- [ ] T040 [P] Memory usage test: Reasonable memory consumption in `/Users/hakankilicaslan/Git/gedit/tests/performance/test_memory_usage.py`
- [ ] T041 [P] Unit tests for validation utility functions in `/Users/hakankilicaslan/Git/gedit/tests/unit/test_validation_utils.py`
- [ ] T042 [P] Update parser documentation and docstrings in `/Users/hakankilicaslan/Git/gedit/app/gcode_parser.py`
- [ ] T043 Run quickstart validation procedures from `/Users/hakankilicaslan/Git/gedit/specs/003-gcode-parser-enhancements/quickstart.md`
- [ ] T044 Final regression test: All existing tests still pass

## Dependencies

### Critical Path (Sequential)
1. **Setup** (T001-T003) → **Contract Tests** (T004-T015) → **Core Implementation** (T016-T030)
2. **Modal State Foundation** (T016-T019) enables all other enhancements
3. **Core Implementation** (T016-T030) → **Integration Tests** (T031-T035) → **System Integration** (T036-T038) → **Performance/Polish** (T039-T044)

### Parallel Opportunities
- **Contract Tests** (T004-T015): All can run in parallel (different files)
- **Integration Tests** (T031-T035): All can run in parallel (different files)  
- **Performance Tests** (T039-T041): Can run in parallel (different files)

### Implementation Dependencies
- T017-T019 (Modal State) must complete before T020-T030 (other enhancements)
- T020-T023 (Arc Processing) can run parallel to T024-T028 (other features)
- T029-T030 (Error Reporting) should be last as it touches all areas

## Parallel Execution Examples

### Contract Test Phase (T004-T015)
```bash
# Launch all contract tests together:
pytest tests/contract/test_modal_state_init.py &
pytest tests/contract/test_modal_state_persistence.py &
pytest tests/contract/test_modal_state_reset.py &
pytest tests/contract/test_arc_r_precedence.py &
pytest tests/contract/test_arc_ijk_calculation.py &
pytest tests/contract/test_arc_plane_validation.py &
pytest tests/contract/test_coordinate_warnings.py &
pytest tests/contract/test_units_validation.py &
pytest tests/contract/test_header_detection.py &
pytest tests/contract/test_footer_detection.py &
pytest tests/contract/test_enhanced_diagnostics.py &
pytest tests/contract/test_context_rich_errors.py &
wait
```

### Integration Test Phase (T031-T035)
```bash
# Launch integration tests together:
pytest tests/integration/test_complex_modal_scenarios.py &
pytest tests/integration/test_mixed_arc_scenarios.py &
pytest tests/integration/test_cam_output_parsing.py &
pytest tests/integration/test_large_coordinate_validation.py &
pytest tests/integration/test_program_structure_detection.py &
wait
```

## Task Generation Rules Applied

✅ **Contract-First**: Every enhancement has contract tests before implementation  
✅ **Parallel Marking**: All independent test files marked [P]  
✅ **TDD Order**: Tests (T004-T015) before implementation (T016-T030)  
✅ **Dependencies**: Modal state foundational, others parallel where possible  
✅ **File Paths**: Exact paths provided for all tasks  
✅ **Backward Compatibility**: Explicit testing (T038) and validation (T043-T044)

## Validation Checklist

- [x] All contracts have tests: Modal state (3), Arc processing (3), Validation (2), Structure (2), Errors (2)
- [x] All entities have models: ModalState, ValidationResult, ArcValidation, ProgramStructure
- [x] All enhancements implemented: 5 key areas from research.md
- [x] Integration tested: Editor, preview, backward compatibility
- [x] Performance validated: Large files, memory usage
- [x] Documentation updated: Docstrings and quickstart validation

**Total Tasks**: 44  
**Estimated Time**: 15-20 hours for experienced developer  
**Parallel Opportunities**: 24 tasks can run in parallel (contract tests + integration tests + performance tests)  
**Critical Path**: Setup → Contract Tests → Modal State Implementation → Other Features → Integration → Polish
