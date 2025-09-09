import tkinter as tk

def create_main_window(root, new_file_command, load_file_command, save_file_command, exit_command):
    """
    Ana menü çubuğunu oluşturur ve döndürür.
    :param root: Tkinter ana pencere
    :param new_file_command: Yeni dosya komutu
    :param load_file_command: Dosya aç komutu
    :param save_file_command: Dosya kaydet komutu
    :param exit_command: Çıkış komutu
    :return: tk.Menu
    """
    """Ana menü çubuğunu oluşturur."""
    menu_bar = tk.Menu(root)
    
    # File menüsü
    file_menu = tk.Menu(menu_bar, tearoff=0)
    file_menu.add_command(label="New", command=new_file_command, accelerator="Ctrl+N")
    file_menu.add_command(label="Open", command=load_file_command, accelerator="Ctrl+O")
    file_menu.add_command(label="Save", command=save_file_command, accelerator="Ctrl+S")
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=exit_command, accelerator="Alt+F4")
    menu_bar.add_cascade(label="File", menu=file_menu)
    
    # Edit menüsü
    edit_menu = tk.Menu(menu_bar, tearoff=0)
    # Platforma göre accelerator metinleri
    is_macos = root.tk.call('tk', 'windowingsystem') == 'aqua'
    undo_acc = 'Cmd+Z' if is_macos else 'Ctrl+Z'
    redo_acc = 'Shift+Cmd+Z' if is_macos else 'Ctrl+Y'

    # Undo/Redo
    edit_menu.add_command(label="Undo", command=lambda: root.focus_get().event_generate("<Command-z>" if is_macos else "<Control-z>"), accelerator=undo_acc)
    edit_menu.add_command(label="Redo", command=lambda: root.focus_get().event_generate("<Shift-Command-Z>" if is_macos else "<Control-y>"), accelerator=redo_acc)
    edit_menu.add_separator()
    # Clipboard işlemleri
    edit_menu.add_command(label="Cut", command=lambda: root.focus_get().event_generate("<<Cut>>"), accelerator="Ctrl+X" if not is_macos else "Cmd+X")
    edit_menu.add_command(label="Copy", command=lambda: root.focus_get().event_generate("<<Copy>>"), accelerator="Ctrl+C" if not is_macos else "Cmd+C")
    edit_menu.add_command(label="Paste", command=lambda: root.focus_get().event_generate("<<Paste>>"), accelerator="Ctrl+V" if not is_macos else "Cmd+V")
    edit_menu.add_separator()
    edit_menu.add_command(label="Show Suggestions", command=lambda: getattr(root.focus_get(), 'force_suggestions', lambda: None)(), accelerator="Ctrl+Space")
    menu_bar.add_cascade(label="Edit", menu=edit_menu)
    
    return menu_bar

# Buton çerçevesini ve butonları oluşturma fonksiyonu (isteğe bağlı, main.py'de de kalabilir)
# def create_button_frame(root, check_syntax_command, preview_command):
#     button_frame = tk.Frame(root)
#     button_frame.pack(pady=5)
#     tk.Button(button_frame, text="Check Syntax", command=check_syntax_command).pack(side=tk.LEFT, padx=5)
#     tk.Button(button_frame, text="Preview", command=preview_command).pack(side=tk.LEFT, padx=5)
#     return button_frame
