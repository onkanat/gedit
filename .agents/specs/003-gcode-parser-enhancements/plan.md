# Implementation Plan: G-code Parser Enhancements

**Branch**: `003-gcode-parser-enhancements` | **Date**: 2025-09-21 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/Users/hakankilicaslan/Git/gedit/specs/003-gcode-parser-enhancements/spec.md`

## ## Progress Tracking
*This checklist is updated during execution flow*

**Phase Completion Status:**

- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command) 
- [x] Phase 2: Task planning approach defined (/plan command)
- [ ] Phase 2: Tasks generated (/tasks command)
- [ ] Phase 3: Implementation execution (manual/tools)
- [ ] Phase 4: Validation & integration (manual/tools)

**Constitutional Compliance:**

- [x] Initial Constitution Check: PASS
- [ ] Post-Design Constitution Check: PENDING (to be done during /tasks)
- [ ] Final Constitution Verification: PENDING

**File Generation Status:**

- [x] research.md created with comprehensive findings
- [x] data-model.md created with backward-compatible extensions  
- [x] contracts/parser.md created with enhanced contract specification
- [x] quickstart.md created with validation procedures
- [ ] tasks.md (awaiting /tasks command)/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
4. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
5. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, or `GEMINI.md` for Gemini CLI).
6. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
7. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
8. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary

Enhance the G-code parser with robust modal state management, improved arc processing with proper I/J/K calculations, program structure detection, coordinate validation, and better error reporting. Implementation inspired by patterns from the Gerber2nc project while maintaining compatibility with existing editor and preview components.

## Technical Context
**Language/Version**: Python 3.11+  
**Primary Dependencies**: No new dependencies required, using existing Python standard library  
**Storage**: N/A (parser works with in-memory strings)  
**Testing**: pytest with existing test structure  
**Target Platform**: Cross-platform (Windows, macOS, Linux) - existing Tkinter support  
**Project Type**: Single project - extending existing parser library  
**Performance Goals**: Parse files up to 100K lines without noticeable delays (<1 second)  
**Constraints**: Must maintain existing output format `{"paths": [...], "layers": [...]}`, backwards compatibility required  
**Scale/Scope**: Enhance existing 500-line parser module with ~200 lines of additional functionality  

**Technical Context from Arguments**: G-code parser improvements inspired by Gerber2nc project patterns including modal state management, arc center calculations, program structure detection, coordinate validation, and enhanced error reporting.

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Simplicity**:
- Projects: 1 (parser enhancement only)
- Using framework directly? (Yes, using existing Python patterns)
- Single data model? (Yes, extending existing parse result structure)
- Avoiding patterns? (Yes, no new architectural patterns)

**Architecture**:
- EVERY feature as library? (Yes, parser module is standalone library)
- Libraries listed: gcode_parser (enhanced G-code parsing with modal states and validation)
- CLI per library: N/A (parser is used by GUI application)
- Library docs: Will add docstring documentation

**Testing (NON-NEGOTIABLE)**:
- RED-GREEN-Refactor cycle enforced? (Yes, will write failing tests first)
- Git commits show tests before implementation? (Yes, will ensure test commits precede implementation)
- Order: Contract→Integration→E2E→Unit strictly followed? (Yes, will follow TDD order)
- Real dependencies used? (Yes, testing actual parser with real G-code)
- Integration tests for: Enhanced parser functionality, contract changes
- FORBIDDEN: Implementation before test, skipping RED phase

**Observability**:
- Structured logging included? (Parser uses diagnostic messages for error reporting)
- Frontend logs → backend? (N/A, GUI application)
- Error context sufficient? (Yes, enhanced error messages with line numbers and context)

**Versioning**:
- Version number assigned? (Will be part of application version, no separate parser version)
- BUILD increments on every change? (Following existing project versioning)
- Breaking changes handled? (Maintaining backward compatibility with existing output format)

## Project Structure

### Documentation (this feature)
```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
# Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure]
```

**Structure Decision**: Single project (Option 1) - enhancing existing parser module within current app structure

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:
   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Each story → integration test scenario
   - Quickstart test = story validation steps

5. **Update agent file incrementally** (O(1) operation):
   - Run `/scripts/update-agent-context.sh [claude|gemini|copilot]` for your AI assistant
   - If exists: Add only NEW tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `/templates/tasks-template.md` as base structure
- Generate TDD-ordered tasks from Phase 1 design artifacts
- Prioritize contract tests (failing) before implementation
- Break down enhancements into focused, testable units

**Enhancement-Specific Task Categories**:

1. **Modal State Management Tasks**:
   - Contract test: Modal state initialization defaults [P]
   - Contract test: Modal state persistence across lines [P]
   - Contract test: Modal state reset on M30/M2 [P]
   - Implementation: Enhanced modal state tracking
   - Integration test: Modal states with complex G-code programs

2. **Arc Processing Enhancement Tasks**:
   - Contract test: R parameter precedence over I/J/K [P]
   - Contract test: Arc center calculation from I/J/K offsets [P]
   - Contract test: Work plane validation for arc parameters [P]
   - Implementation: Improved arc processing logic
   - Integration test: Mixed arc parameter scenarios

3. **Program Structure Detection Tasks**:
   - Contract test: Header pattern detection [P]
   - Contract test: Footer pattern detection [P]
   - Implementation: Program structure analysis
   - Integration test: Structure detection on various CAM outputs

4. **Coordinate Validation Tasks**:
   - Contract test: Large coordinate warnings [P]
   - Contract test: Units-aware validation [P]
   - Implementation: Coordinate validation system
   - Integration test: Validation with real-world coordinate ranges

5. **Enhanced Error Reporting Tasks**:
   - Contract test: Enhanced diagnostic message templates [P]
   - Contract test: Context-rich error messages [P]
   - Implementation: Improved error reporting system
   - Integration test: Error message quality with malformed input

**Task Ordering Strategy**:
- TDD Strict Order: RED (failing test) → GREEN (minimal implementation) → REFACTOR
- Dependencies: Modal state management foundational, others can be parallel
- Integration tests after all contract implementations complete
- Backward compatibility validation at each step

**Parallel Execution Markers [P]**:
- All contract tests can be written in parallel (independent)
- Modal state and arc processing can be implemented in parallel
- Structure detection and coordinate validation independent
- Error reporting touches all areas, implement last

**Estimated Output**: 
- 5 foundational contract tests (parallel)
- 15-20 specific feature contract tests (parallel by feature)
- 5 main implementation tasks (some parallel)
- 8-10 integration tests
- 3-5 backward compatibility validation tests
- **Total: ~35-40 ordered tasks**

**Quality Gates**:
- Each implementation task must make its contract tests pass
- Integration tests validate real-world usage patterns
- Performance tests ensure <1s parsing for 100K lines
- Backward compatibility tests prevent regressions

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |


## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [ ] Post-Design Constitution Check: PASS  
- [x] All NEEDS CLARIFICATION resolved
- [ ] Complexity deviations documented

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*
