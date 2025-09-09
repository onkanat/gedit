import tkinter as tk
from app.editor import GCodeEditor


def make_root():
    root = tk.Tk()
    try:
        root.withdraw()
    except Exception:
        pass
    return root


def make_editor():
    root = make_root()
    editor = GCodeEditor(root, wrap=tk.NONE, undo=True)
    editor.pack()
    return root, editor
