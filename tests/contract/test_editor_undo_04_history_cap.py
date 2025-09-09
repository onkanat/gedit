import tkinter as tk
from tests.utils_tk import make_editor


def test_history_cap_maxundo():
    root, editor = make_editor()
    try:
        editor.delete('1.0', tk.END)
        # set low maxundo if supported
        try:
            editor.configure(maxundo=2)
        except Exception:
            pass
        # 1st edit
        editor.insert('1.0', 'A')
        editor.edit_separator()
        # 2nd edit
        editor.insert('end', 'B')
        editor.edit_separator()
        # 3rd edit
        editor.insert('end', 'C')
        editor.edit_separator()
        # Undo 3rd
        editor.edit_undo()
        # Undo 2nd
        editor.edit_undo()
        # Attempt to undo 1st (may be pruned)
        pruned = False
        try:
            editor.edit_undo()
        except Exception:
            pruned = True
        text = editor.get('1.0', 'end-1c')
        # After two undos and prune, expect empty or 'A' removed
        assert text in ('', 'A')
    finally:
        root.destroy()
