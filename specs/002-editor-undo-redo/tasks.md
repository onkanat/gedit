# Tasks: Editor Undo/Redo & Basics

Input: Design documents from `/specs/002-editor-undo-redo/`

Prerequisites: plan.md (required), research.md, data-model.md, contracts/

Feature Dir: /Users/hakankilicaslan/Git/gedit/specs/002-editor-undo-redo

Notes:

- All file paths below are absolute.
- Tests first (they WILL fail) → then implementation.

## Phase 3.1: Setup

- [ ] T001 Verify environment and deps
  - Ensure pytest works and Tkinter is available
  - Files: /Users/hakankilicaslan/Git/gedit/requirements.txt
- [ ] T002 [P] Add test helper for Tk root
  - Create helper to manage Tk lifecycle in tests (withdraw root)
  - File: /Users/hakankilicaslan/Git/gedit/tests/utils_tk.py

## Phase 3.2: Tests First (TDD)

CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation.

Contract tests (from contracts/editor_undo.md):

- [ ] T003 [P] Contract test: Undo after typed text
  - File: /Users/hakankilicaslan/Git/gedit/tests/contract/test_editor_undo_01_typed_text.py
  - Asserts: two chunks typed → undo once → first chunk remains
- [ ] T004 [P] Contract test: Grouping with separator on Enter
  - File: /Users/hakankilicaslan/Git/gedit/tests/contract/test_editor_undo_02_group_on_enter.py
  - Asserts: separator on Enter groups previous edits
- [ ] T005 [P] Contract test: Redo reapplies
  - File: /Users/hakankilicaslan/Git/gedit/tests/contract/test_editor_undo_03_redo.py
  - Asserts: redo restores last undone chunk
- [ ] T006 [P] Contract test: History cap (maxundo)
  - File: /Users/hakankilicaslan/Git/gedit/tests/contract/test_editor_undo_04_history_cap.py
  - Asserts: with maxundo=2, 3 edits → first cannot be undone

Integration tests (user stories from quickstart):

- [ ] T007 [P] Integration: Keyboard shortcuts trigger undo/redo
  - File: /Users/hakankilicaslan/Git/gedit/tests/integration/test_editor_shortcuts.py
  - Asserts: Cmd/Ctrl shortcuts call editor.undo/redo (may use event_generate)

## Phase 3.3: Core Implementation (ONLY after tests are failing)

- [ ] T008 Implement undo API in editor
  - Methods in /Users/hakankilicaslan/Git/gedit/app/editor.py:
    - enable_undo(max_undo: int = 1000)
    - disable_undo()
    - undo() -> bool, redo() -> bool
    - add_undo_separator(), clear_history()
  - Update EditorState attributes per data-model.md
- [ ] T009 Bind keyboard shortcuts (cross-platform)
  - macOS: Cmd+Z, Shift+Cmd+Z; Win/Linux: Ctrl+Z, Ctrl+Y
  - File: /Users/hakankilicaslan/Git/gedit/app/editor.py
- [ ] T010 Grouping separators on events
  - Add separators on Enter, paste, focus-out
  - Implement idle-timer separator (~800ms) via after()
  - File: /Users/hakankilicaslan/Git/gedit/app/editor.py
- [ ] T011 Preserve existing features
  - Ensure autocomplete, tooltip, diagnostics unaffected
  - File: /Users/hakankilicaslan/Git/gedit/app/editor.py

## Phase 3.4: Integration

- [ ] T012 Wire Undo/Redo menu items
  - Add/Edit menu actions and accelerators
  - File: /Users/hakankilicaslan/Git/gedit/app/gui.py

## Phase 3.5: Polish

- [ ] T013 [P] Add README shortcuts section
  - Update docs to mention Undo/Redo shortcuts and behavior
  - File: /Users/hakankilicaslan/Git/gedit/README.md
- [ ] T014 [P] Add unit test for idle separator
  - Validate separator added after inactivity (may stub timer)
  - File: /Users/hakankilicaslan/Git/gedit/tests/unit/test_idle_separator.py
- [ ] T015 [P] Update quickstart if needed
  - Ensure quickstart reflects final bindings and API
  - File: /Users/hakankilicaslan/Git/gedit/specs/002-editor-undo-redo/quickstart.md

## Dependencies

- T001 before all tests
- T002 before T003–T007
- T003–T007 before T008–T011 (TDD)
- T008 blocks T009–T011
- T011 before T012
- Implementation before polish (T013–T015)

## Parallel Execution Examples

```text
# Launch contract tests creation in parallel (different files):
Task: "T003 Contract test: Undo after typed text"
Task: "T004 Contract test: Grouping with separator on Enter"
Task: "T005 Contract test: Redo reapplies"
Task: "T006 Contract test: History cap (maxundo)"

# Launch polish tasks in parallel after implementation:
Task: "T013 Add README shortcuts section"
Task: "T014 Add unit test for idle separator"
Task: "T015 Update quickstart if needed"
```

## Task Agent Commands (examples)

- Run all tests: pytest -q
- Run a single test file: pytest -q /Users/hakankilicaslan/Git/gedit/tests/contract/test_editor_undo_01_typed_text.py
- Lint markdown (optional): markdownlint-cli2 '**/*.md'
