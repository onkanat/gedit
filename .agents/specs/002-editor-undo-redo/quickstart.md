# Quickstart: Editor Undo/Redo

Date: 2025-09-09

## Shortcuts

- macOS
  - Cmd+Z: Undo
  - Shift+Cmd+Z: Redo
- Windows/Linux
  - Ctrl+Z: Undo
  - Ctrl+Y: Redo

## Enabling

- Editor is created with `undo=True` already via `create_text_editor`.
- To ensure generous history: configure `maxundo` (e.g., 1000).

## API

- editor.undo()
- editor.redo()
- editor.add_undo_separator()
- editor.clear_history()

## Tips

- Separators are automatically added on Enter and paste; you can add your own to group changes.
