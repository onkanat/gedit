# Spec: Editor Undo/Redo & Basics

Date: 2025-09-09

## Objective

Implement robust undo/redo behavior in `app/editor.py` (GCodeEditor) using Tk Text built-ins, with sensible grouping and cross-platform shortcuts, without regressing autocomplete/tooltip/diagnostics.

## Scope (Must)

- Enable built-in undo stack with configurable `maxundo` (default 1000).
- Provide methods:
  - `enable_undo(max_undo: int = 1000)`
  - `disable_undo()`
  - `undo()` and `redo()` returning success boolean
  - `add_undo_separator()`
  - `clear_history()`
- Add keybindings:
  - macOS: Cmd+Z (undo), Shift+Cmd+Z (redo)
  - Win/Linux: Ctrl+Z (undo), Ctrl+Y (redo)
- Grouping policy:
  - Separator on Enter, paste, focus-out
  - Idle-time separator after ~800ms inactivity
- Keep UI responsive (use `after()` timers; avoid heavy work on key events).

## Out-of-Scope (Won't)

- Custom diff-based undo stacks
- Persistent undo history across sessions

## Acceptance Criteria

1. Typing two chunks then undo once removes the last chunk as a group.
2. Redo re-applies the last undone chunk.
3. With `maxundo=2`, making 3 separated edits prunes the first change.
4. Shortcuts work on macOS and Windows/Linux.
5. Existing features (autocomplete window, tooltips, diagnostics highlighting) keep working.

## Risks & Mitigations

- Overridden `insert` method: ensure separators still applied on key events and timer; keep override lightweight.
- Platform differences in Tk autoseparators: rely on explicit `edit_separator()` calls.
