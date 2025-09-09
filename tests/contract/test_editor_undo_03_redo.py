import tkinter as tk
from tests.utils_tk import make_editor


def test_redo_reapplies_last_chunk():
    root, editor = make_editor()
    try:
        editor.delete('1.0', tk.END)
        editor.insert('1.0', 'G1 X10')
        try:
            editor.edit_separator()
        except Exception:
            pass
        editor.insert('end', '\nG1 Y20')
        # undo once
        editor.edit_undo()
        # redo should bring back last chunk
        editor.edit_redo()
        text = editor.get('1.0', 'end-1c')
        assert text.strip().endswith('G1 Y20')
    finally:
        root.destroy()
