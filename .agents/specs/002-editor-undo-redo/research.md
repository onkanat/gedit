# Research: Tk Text Undo/Redo for GCodeEditor

Date: 2025-09-09

## Goals

- Reliable undo/redo with sensible grouping.
- Low risk: Prefer built-in Tk Text mechanisms over custom stacks.

## Tk Text Undo API Overview

- `Text(undo=True)`: Enables built-in undo stack.
- `edit_undo() / edit_redo()`: Perform undo/redo.
- `edit_separator()`: Insert a separator to group subsequent edits into a new undo block.
- `edit_modified([bool])`: Query/set modified flag; can be used to mark save points.
- `edit_reset()`: Clears the undo/redo stacks (use with care).
- `edit_modified` events can be observed via `<<Modified>>` virtual event.

Notes:

- Autoseparators: When `undo=True`, Tk automatically adds separators for operations like newline insertion; frequency can vary by platform/Tk version.
- Max undo depth: Tk has `-maxundo` option; in Tkinter available via widget option `maxundo` on creation or `.configure(maxundo=n)`.
- Programmatic inserts via `Text.insert` and deletions via `Text.delete` participate in stack when `undo=True`.

## Grouping Strategy

- Always call `edit_separator()` on:
  - Return/Enter
  - After paste
  - After a pause longer than `group_threshold_ms` (e.g., 800ms) between keypresses
  - On focus-out
- Allow manual separators via API `add_undo_separator()`.
- Avoid excessive separators (throttle to once per event boundary).

## Keybindings

- macOS:
  - Cmd+Z: undo
  - Shift+Cmd+Z: redo (preferred on macOS)
- Windows/Linux:
  - Ctrl+Z: undo
  - Ctrl+Y: redo
- Bind both sets to be cross-platform.

## Limits & Pruning

- Set `maxundo` to a moderate default (e.g., 1000 operations) to avoid memory bloat.
- Provide `clear_history()` to call `edit_reset()` after optionally setting a savepoint.

## Pitfalls

- Overriding `Text.insert` can bypass default autoseparators; ensure we either:
  - Call `super().insert()` and then rely on explicit `edit_separator()` calls, or
  - Minimize heavy logic inside overridden insert to keep performance.
- Our editor currently overrides `insert` to uppercase G-code letters and tag them; this is fine as long as we still call `super().insert` and we add separators where needed (Return/Paste/Blur/Timer).
- Be careful not to call `edit_reset()` while user expects redo to be available.

## Decision Summary

- Use Tk built-in undo (`undo=True`) and configure `maxundo`.
- Implement grouping via explicit separators on key events and short timer-based idle separator.
- Provide API: enable/disable undo, undo/redo, clear_history, add_undo_separator.
- Add keybindings and optional menu hooks.
