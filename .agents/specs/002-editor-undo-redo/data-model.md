# Data Model: Editor Undo/Redo

Date: 2025-09-09

## Entities

- EditorState
  - undo_enabled: bool
  - max_undo: int (default 1000)
  - group_threshold_ms: int (default 800)
  - autoseparators: bool (default True)
  - last_edit_ts: float | None

## Methods (contracts)

- enable_undo(max_undo: int = 1000) -> None
  - Sets `undo=True` and configures `maxundo`. Binds key shortcuts.
- disable_undo() -> None
  - Disables undo if possible and unbinds shortcuts.
- undo() -> bool
  - Performs `edit_undo()` if available; returns True if changed, False otherwise.
- redo() -> bool
  - Performs `edit_redo()` if available; returns True if changed, False otherwise.
- add_undo_separator() -> None
  - Calls `edit_separator()` safely.
- clear_history() -> None
  - Calls `edit_reset()` safely.

## Keybindings

- Cmd+Z / Ctrl+Z → undo
- Shift+Cmd+Z / Ctrl+Y → redo

## Events and Grouping

- On `Return`, `FocusOut`, and after paste → add separator
- Timer-based idle separator when time since last edit > group_threshold_ms
