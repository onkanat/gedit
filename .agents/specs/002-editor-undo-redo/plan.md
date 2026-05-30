# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]
**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

## Execution Flow (/plan command scope)
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
# Implementation Plan: Editor Undo/Redo & Basics

**Branch**: `002-editor-undo-redo` | **Date**: 2025-09-09 | **Spec**: /specs/002-editor-undo-redo/spec.md (TBD)
**Input**: Feature specification from `/specs/002-editor-undo-redo/spec.md`

## Execution Flow (/plan command scope)

1. Load feature spec from Input path
   → If not found: proceed with plan using this file as source of truth; create spec stub
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Project type: single desktop app (Tkinter)
3. Evaluate Constitution Check section below
   → Simplicity/Testing gates OK
   → Update Progress Tracking: Initial Constitution Check
4. Execute Phase 0 → research.md (Tk Text undo API, grouping, limits)
5. Execute Phase 1 → contracts/, data-model.md, quickstart.md
6. Re-evaluate Constitution Check section → PASS
7. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
8. STOP - Ready for /tasks command

## Summary

- Add robust undo/redo, edit history management, and a few basic editor niceties to `app/editor.py`.
- Keep UI responsive (Tkinter after/throttle), preserve existing autocomplete/tooltip behavior.

## Technical Context

- Language/Version: Python 3.13 + Tkinter
- Primary Dependencies: stdlib Tkinter/ttk only (no extra libs)
- Storage: N/A
- Testing: pytest (add small unit/integration tests for undo/redo stack behavior)
- Target Platform: macOS (Tk on mac), cross-platform friendly
- Project Type: single desktop app
- Performance Goals: Undo/redo within <5ms per op for typical lines; no visible UI jank
- Constraints: Avoid heavy operations on UI thread; no third-party editors

## Constitution Check

- Simplicity: Single module changes; use Tk Text built-in undo as baseline
- Architecture: No new packages; feature stays in editor module
- Testing: Add tests that simulate insert/delete and verify undo/redo stack depth
- Observability: Optional debug logs guarded behind flag
- Versioning: Minor feature, non-breaking

## Project Structure

### Documentation (this feature)

```text
specs/002-editor-undo-redo/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
└── contracts/           # Phase 1 output (/plan command)
```

## Phase 0: Outline & Research

Unknowns:

- Tk Text built-in undo versus custom stack: capabilities and limits
- Grouping edits (Ctrl+Z granularity)
- Memory usage limits and pruning

Tasks:

- Research Tk Text undo options (edit_undo/edit_redo, edit_separator, maxundo)
- Decide grouping strategy (on Return/Space/blur)
- Decide pruning policy (cap stack by operations count)

## Phase 1: Design & Contracts

Entities/State:

- EditorState: { undo_enabled: bool, max_undo: int, group_threshold_ms: int }
- Actions: insert/delete/replace; separators to group

API/Controls:

- Methods on GCodeEditor:
  - enable_undo(max_undo=1000)
  - disable_undo()
  - undo(), redo()
  - add_undo_separator()
  - clear_history()
- Keybindings:
  - Cmd+Z / Ctrl+Z → undo
  - Shift+Cmd+Z / Ctrl+Y → redo

Contract tests:

- After a sequence of inserts, undo restores previous text
- Separators group multiple inserts into a single undo step
- Redo reapplies last undone changes

Quickstart additions:

- Mention keyboard shortcuts and menu hooks

## Phase 2: Task Planning Approach

- Generate tasks from contracts (tests for undo/redo/sep)
- Implement editor methods and bindings
- Wire optional menu items in gui.py

## Progress Tracking

- [ ] Phase 0: Research complete (/plan command)
- [ ] Phase 1: Design complete (/plan command)
- [ ] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Initial Constitution Check: PASS
- [ ] Post-Design Constitution Check: PASS
