# AGENTS.md - G-code Editor Repository Guide

## Build/Test Commands
- **Run app**: `python app/main.py`
- **Run all tests**: `python -m pytest tests/`
- **Run single test**: `python -m pytest tests/test_gcode_parser.py::TestGCodeParser::test_linear_moves_and_modal`
- **Run contract tests**: `python -m pytest tests/contract/`
- **Run integration tests**: `python -m pytest tests/integration/`

## Code Style Guidelines
- **Language**: Python 3.12+ with PEP 8 compliance
- **Imports**: Standard library first, then third-party, then local app modules
- **Type hints**: Use type hints for function signatures and complex data structures
- **Naming**: snake_case for variables/functions, PascalCase for classes
- **Error handling**: Use .get() for dict access, structured error reporting with severity levels
- **Parser output**: Must return `{"paths": [...], "layers": [...]}` structure with line_no and line fields
- **Arc validation**: R parameter takes precedence over IJK, plane-aware calculations (G17/G18/G19)
- **UI threading**: Use `after()` for heavy operations to prevent UI blocking
- **File structure**: Core modules in app/, tests in tests/, data definitions in app/data/

## Key Architecture Rules
- Editor: Preserve event attributes, use None checks, auto-capitalize G-code letters
- Parser: Modal state tracking, comprehensive arc validation, continue parsing after errors
- Preview: Only draw valid paths with numeric validation, 2D plane selector (Auto/G17/G18/G19)
- GUI: Turkish comments preferred, structured diagnostic messages with recovery suggestions