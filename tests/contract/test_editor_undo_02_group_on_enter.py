import tkinter as tk
from tests.utils_tk import make_editor


def test_grouping_with_enter_separator():
    root, editor = make_editor()
    try:
        editor.delete('1.0', tk.END)
        editor.insert('1.0', 'G1 X10')
        # simulate Enter separator
        try:
            editor.edit_separator()
        except Exception:
            pass
        editor.insert('end', '\n')
        editor.insert('end', 'G1 Y20')
        # now undo should remove last line chunk
        try:
            editor.edit_undo()
        except Exception:
            pass
        text = editor.get('1.0', 'end-1c')
        assert text.strip().split('\n')[-1] == 'G1 X10'
    finally:
        root.destroy()
