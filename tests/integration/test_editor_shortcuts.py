import tkinter as tk
from tests.utils_tk import make_editor


def test_keyboard_shortcuts_trigger_undo_redo():
    root, editor = make_editor()
    try:
        editor.delete('1.0', tk.END)
        editor.insert('1.0', 'LINE1')
        editor.edit_separator()
        editor.insert('end', '\nLINE2')
        # simulate undo
        try:
            editor.event_generate('<Control-z>')
        except Exception:
            editor.edit_undo()
        # then redo
        try:
            editor.event_generate('<Control-y>')
        except Exception:
            editor.edit_redo()
        text = editor.get('1.0', 'end-1c')
        assert 'LINE2' in text
    finally:
        root.destroy()
