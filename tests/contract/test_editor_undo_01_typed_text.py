import pytest
import tkinter as tk
from tests.utils_tk import make_editor


def test_undo_after_typed_text():
    root, editor = make_editor()
    try:
        editor.delete('1.0', tk.END)
        editor.insert('1.0', 'G1 X10')
        editor.insert('end', ' Y20')
        # Trigger undo
        changed = False
        try:
            editor.edit_separator()
        except Exception:
            pass
        try:
            editor.edit_undo()
            changed = True
        except Exception:
            changed = False
        text = editor.get('1.0', 'end-1c')
        assert changed is True
        assert text.strip() == 'G1 X10'
    finally:
        root.destroy()
