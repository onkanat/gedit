import tkinter as tk
from tkinter import ttk
import re
import json
import os
import time


class LineNumbers(tk.Canvas):
    """
    Canvas widget for displaying line numbers in the G-code editor.

    This class integrates with a Text widget to show line numbers that
    scroll synchronously with the text content. It provides visual feedback
    for code navigation and debugging purposes.

    Attributes:
        text_widget (tk.Text): The associated text widget for line tracking
    """

    def __init__(self, parent, text_widget, *args, **kwargs):
        """
        Initialize the line numbers canvas.

        Args:
            parent: Parent widget (typically the main window or frame)
            text_widget (tk.Text): The text widget to track for line numbers
            *args: Additional positional arguments for Canvas
            **kwargs: Additional keyword arguments for Canvas
        """
        super().__init__(parent, width=30, *args, **kwargs)
        self.text_widget = text_widget
        self.redraw()  # Initial drawing

        # Bind to text widget scroll and change events
        # Redraw is called only on necessary events for performance throttling
        self.text_widget.bind("<KeyRelease>", self.redraw)
        self.text_widget.bind("<MouseWheel>", self.redraw)
        self.text_widget.bind("<Configure>", self.redraw)
        self.text_widget.bind("<ButtonRelease-1>", self.redraw)

    def redraw(self, *args):
        """
        Redraw line numbers based on visible text area.

        Clears the canvas and redraws line numbers for the currently
        visible portion of the text widget. Uses efficient calculation
        to only draw numbers that are actually visible.

        Args:
            *args: Event arguments (ignored, for binding compatibility)
        """
        self.delete("all")  # Canvas'ı temizle

        # Görünür alan hesaplaması
        first_line = self.text_widget.index("@0,0")
        last_line = self.text_widget.index(f"@0,{self.text_widget.winfo_height()}")

        first_line_num = int(float(first_line))
        last_line_num = int(float(last_line)) + 1

        # Her satır için numara çiz
        for line_num in range(first_line_num, last_line_num):
            dline = self.text_widget.dlineinfo(f"{line_num}.0")
            if dline:  # Eğer satır görünürse
                y = dline[1]  # Y koordinatı
                self.create_text(
                    15,  # X koordinatı (ortalanmış)
                    y,  # Y koordinatı
                    text=str(line_num),
                    anchor="n",
                    fill="gray50",
                    font=self.text_widget["font"],
                )


class EditorFrame(tk.Frame):
    """
    Main frame wrapper for the editor component.

    This class encapsulates the GCodeEditor widget and provides
    a clean interface for external access. It serves as a container
    that can be easily integrated into larger GUI applications.

    Attributes:
        editor (GCodeEditor): The actual G-code editor widget instance
    """

    def __init__(self, master=None, **kwargs):
        """
        Initialize the editor frame.

        Args:
            master: Parent widget (typically main window or container)
            **kwargs: Additional keyword arguments passed to GCodeEditor
        """
        super().__init__(master)
        self.editor = GCodeEditor(self, **kwargs)

    def get_editor(self):
        """
        Get the editor instance.

        Returns:
            GCodeEditor: The G-code editor widget instance contained in this frame
        """
        return self.editor


class GCodeEditor(tk.Text):
    """
    Enhanced Tkinter Text widget customized for G-code editing.

    This widget provides comprehensive G-code editing capabilities including:
    - Auto-completion with G-code command suggestions
    - Line numbers display
    - Syntax highlighting for G-code letters
    - Tooltips with command descriptions and error diagnostics
    - Undo/redo functionality with intelligent grouping
    - Keyboard shortcuts and navigation
    - Integration with enhanced parser diagnostics

    Attributes:
        suggestions_window: Toplevel window for auto-completion suggestions
        _suggestion_listbox: Listbox widget for suggestion display
        tooltip: Toplevel window for command tooltips
        keywords: Cached G-code command definitions
        gcode_letters: Set of valid G-code parameter letters
    """

    def __init__(self, master=None, **kwargs):
        """
        Initialize G-code editor with all features.

        Args:
            master: Parent widget (typically main window or frame)
            **kwargs: Additional keyword arguments for Text widget
        """
        # Default font setting
        if "font" not in kwargs:
            kwargs["font"] = ("Courier", 14)

        # Create Text widget
        super().__init__(master, **kwargs)

        # Scrollbar ve line numbers
        self.scrollbar = ttk.Scrollbar(master, orient="vertical", command=self.yview)
        self.line_numbers = LineNumbers(master, self, bg="#f0f0f0")

        def on_scroll(*args):
            self.scrollbar.set(*args)
            if hasattr(self, "line_numbers"):
                self.line_numbers.redraw()

        self.configure(yscrollcommand=on_scroll)

        # Widget'ları yerleştir
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        self.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Diğer başlangıç ayarları
        self.suggestions_window = None
        self._suggestion_listbox = None
        self.tooltip = None

        # G-code tanımlarını JSON dosyasından yükle (global cache)
        if not hasattr(GCodeEditor, "_gcode_keywords_cache"):
            GCodeEditor._gcode_keywords_cache = self.load_gcode_definitions()
        self.keywords = GCodeEditor._gcode_keywords_cache

        # Text tag'leri oluştur
        self.tag_configure(
            "gcode_letter",
            foreground="blue",
            font=(kwargs["font"][0], kwargs["font"][1], "bold"),
        )
        # Diagnostik etiketleri (hata/uyarı satır vurguları)
        self.tag_configure("error_line", background="#ffefef")
        self.tag_configure("warning_line", background="#fff9db")

        # Event bindings
        self.bind("<KeyPress>", self.handle_keypress)
        self.bind("<KeyRelease>", self.show_suggestions)
        self.bind("<Control-space>", self.force_suggestions)
        self.bind("<Button-1>", self.handle_click)
        self.bind("<Control-x>", self.cut)
        self.bind("<Control-c>", self.copy)
        self.bind("<Control-v>", self.paste)
        self.bind("<Motion>", self.show_tooltip)
        # Enter/Tab özel davranışları
        self.bind("<Return>", self.handle_return)
        self.bind("<Tab>", self.handle_tab)
        # Yapıştırma ve odak değişimi
        self.bind("<<Paste>>", self._on_paste)
        self.bind("<FocusOut>", self._on_focus_out)

        # Undo/Redo ve gruplama durumu
        self.undo_enabled = True
        self.max_undo = 1000
        self.group_threshold_ms = 800
        self._last_edit_ts = 0.0
        self._idle_sep_after_id = None
        try:
            self.configure(undo=True)
            self.configure(maxundo=self.max_undo)
        except Exception:
            pass

        # Kısayollar (platformlar arası)
        self.bind("<Control-z>", self._on_undo)
        self.bind("<Control-y>", self._on_redo)
        self.bind("<Control-Shift-Z>", self._on_redo)
        self.bind("<Command-z>", self._on_undo)
        self.bind("<Shift-Command-Z>", self._on_redo)

        # G-code harfleri listesi
        self.gcode_letters = {
            "g",
            "x",
            "y",
            "z",
            "m",
            "i",
            "j",
            "k",
            "f",
            "r",
            "s",
            "t",
            "n",
        }

    def load_gcode_definitions(self):
        """
        Load G-code command definitions from JSON data file.

        Reads the gcode_definitions.json file from the app/data directory
        and returns a dictionary mapping G-code commands to their descriptions.
        Uses class-level caching to avoid repeated file reads.

        Returns:
            dict: Dictionary with G-code commands as keys and descriptions as values.
                 Returns empty dict if file cannot be loaded or parsed.
        """
        try:
            # Dosya yolunu belirle
            json_path = os.path.join(
                os.path.dirname(__file__), "data", "gcode_definitions.json"
            )

            # JSON dosyasını oku
            with open(json_path, "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception as e:
            print(f"G-code tanımları yüklenemedi: {e}")
            # Hata durumunda varsayılan boş sözlük döndür
            return {}

    def get_current_word(self):
        """
        Get the current word at cursor position.

        Extracts the word fragment from the beginning of the current line
        up to the cursor position. Used for auto-completion context.

        Returns:
            str: The current word fragment at cursor position. Empty string if no word found.
        """
        current_line = self.get("insert linestart", "insert")
        match = re.search(r"[A-Za-z0-9]*$", current_line)
        return match.group(0) if match else ""

    def show_suggestions(self, event=None):
        """
        Show auto-completion suggestions based on current word.

        Triggers on letter or space/backspace key releases. Finds matching
        G-code commands that contain the current word fragment (case-insensitive)
        and displays them in a suggestions window.

        Args:
            event: Keyboard event object (optional). Used to filter trigger events.
        """
        # Sadece harf veya silme tuşlarında tetiklenir
        if event and not (
            event.char.isalpha() or event.keysym in ["space", "BackSpace"]
        ):
            return
        current_word = self.get_current_word()
        if len(current_word) >= 1:
            # startswith yerine substring eşleşme (daha akıllı)
            suggestions = [
                k for k in self.keywords.keys() if current_word.lower() in k.lower()
            ]
            if suggestions:
                self.show_suggestions_window(suggestions)
            elif self.suggestions_window:
                self.close_suggestions()
        elif self.suggestions_window:
            self.close_suggestions()

    def show_suggestions_window(self, suggestions):
        """
        Create or update the auto-completion suggestions popup window.

        Displays a listbox with G-code command suggestions and their descriptions.
        Handles window positioning to stay within screen bounds and updates
        existing window if already open.

        Args:
            suggestions (list): List of G-code command keys to display as suggestions.
        """

        # Yardımcı: Görüntülenecek metni kısalt (uzun açıklamalar pencereyi taşırmasın)
        def _display_text(key: str, max_len: int = 60) -> str:
            desc = str(self.keywords.get(key, ""))
            text = f"{key} - {desc}"
            if len(text) > max_len:
                return text[: max_len - 1] + "…"
            return text

        # Kısa metinleri önceden hazırla ve genişlik/uzunluk sınırlarını hesapla
        display_items = [_display_text(k) for k in suggestions]
        width_chars = max((len(s) for s in display_items), default=24)
        width_chars = max(24, min(50, width_chars))  # 24..50 karakter arası sabitle
        height_rows = min(len(display_items), 8)  # en fazla 8 satır göster
        # Pencere zaten varsa sadece güncelle
        if (
            self.suggestions_window
            and self.suggestions_window.winfo_exists()
            and self._suggestion_listbox
        ):
            listbox = self._suggestion_listbox
            listbox.delete(0, tk.END)
            for display_text in display_items:
                listbox.insert(tk.END, display_text)
            try:
                listbox.configure(width=width_chars, height=height_rows)
            except Exception:
                pass
            listbox.selection_set(0)
            listbox.see(0)
            return

        # Yoksa yeni pencere oluştur
        bbox = self.bbox("insert")
        if not bbox:
            self.update_idletasks()
            bbox = self.bbox("insert")
            if not bbox:
                return
        x, y, _, h = bbox
        x = x + self.winfo_rootx()
        y = y + h + self.winfo_rooty()

        self.suggestions_window = tk.Toplevel()
        self.suggestions_window.wm_overrideredirect(True)
        try:
            # Kök pencereye transient bağla (lint/typecheck uyumu için toplevel kullan)
            self.suggestions_window.transient(self.winfo_toplevel())
        except Exception:
            pass

        listbox = tk.Listbox(
            self.suggestions_window,
            selectmode=tk.SINGLE,
            activestyle="none",
            height=height_rows,
            width=width_chars,
            font=self["font"],
        )
        listbox.pack(fill=tk.BOTH, expand=True)
        for display_text in display_items:
            listbox.insert(tk.END, display_text)
        if listbox.size() > 0:
            listbox.selection_set(0)
            listbox.see(0)
        self._suggestion_listbox = listbox
        # Pencere boyutunu/konumunu ekrana göre sınırla
        self.suggestions_window.update_idletasks()
        req_w = self.suggestions_window.winfo_reqwidth()
        req_h = self.suggestions_window.winfo_reqheight()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        # Sağ kenardan taşarsa sola doğru kaydır
        if x + req_w > screen_w - 8:
            x = max(0, screen_w - req_w - 8)
        # Alt kenardan taşarsa caret üstüne yerleştir
        if y + req_h > screen_h - 8:
            y = max(0, y - req_h - (h if isinstance(h, int) else 0) - 4)
        self.suggestions_window.geometry(f"+{x}+{y}")
        listbox.bind("<Double-Button-1>", self.apply_selected_suggestion)
        listbox.bind("<Return>", self.apply_selected_suggestion)
        listbox.bind("<Escape>", self.close_suggestions)
        listbox.bind("<FocusOut>", lambda e: self.after(100, self.close_suggestions))
        self.suggestions_window.update_idletasks()
        self.suggestions_window.lift()
        self.focus_set()
        listbox.activate(0)
        self.suggestions_window.update()

    def navigate_suggestions(self, event):
        """
        Navigate through suggestions using arrow keys.

        Handles Up/Down arrow key events to move selection in the
        suggestions listbox. Prevents default arrow key behavior.

        Args:
            event: Keyboard event object containing the pressed key.

        Returns:
            str: "break" to prevent further event propagation.
        """
        if not self.suggestions_window or not self._suggestion_listbox:
            return "break"
        listbox = self._suggestion_listbox
        current = listbox.curselection()
        if event.keysym == "Up" and current and current[0] > 0:
            listbox.selection_clear(current)
            new_index = current[0] - 1
            listbox.selection_set(new_index)
            listbox.see(new_index)
        elif event.keysym == "Down" and current and current[0] < listbox.size() - 1:
            listbox.selection_clear(current)
            new_index = current[0] + 1
            listbox.selection_set(new_index)
            listbox.see(new_index)
        return "break"

    def handle_tab(self, event=None):
        """
        Handle Tab key press for auto-completion.

        If suggestions window is open, applies the selected suggestion.
        Otherwise allows default Tab behavior.

        Args:
            event: Keyboard event object (optional).

        Returns:
            str or None: "break" if suggestion was applied, None for default behavior.
        """
        if self.suggestions_window:
            self.apply_selected_suggestion(event)
            return "break"
        return None

    def handle_click(self, event=None):
        """
        Handle mouse click events in the editor.

        Closes the suggestions window when clicking outside of it.
        Allows normal text selection and cursor positioning.

        Args:
            event: Mouse event object (optional).
        """
        if self.suggestions_window and self._suggestion_listbox:
            # Tıklama öneri penceresinde değilse kapat
            if not (
                event
                and hasattr(event, "widget")
                and event.widget == self._suggestion_listbox
            ):
                self.close_suggestions()

    def apply_selected_suggestion(self, event=None):
        """
        Apply the selected suggestion to the editor.

        Replaces the current word fragment with the selected G-code command
        and closes the suggestions window. Handles both double-click and
        Enter key events.

        Args:
            event: Keyboard or mouse event object (optional).

        Returns:
            str: "break" to prevent further event propagation.
        """
        if not self.suggestions_window or not self._suggestion_listbox:
            return "break"
        listbox = self._suggestion_listbox
        selection = listbox.curselection()
        if selection:
            suggestion = listbox.get(selection[0]).split(" - ")[0]
            current_word = self.get_current_word()
            if current_word:
                position = "insert-{}c".format(len(current_word))
                self.delete(position, "insert")
            self.insert("insert", suggestion + " ")
            self.close_suggestions()
            self.see(tk.INSERT)
            self.focus_set()
        return "break"

    def close_suggestions(self, event=None):
        """
        Close the auto-completion suggestions window.

        Destroys the suggestions popup and cleans up references.
        Returns focus to the main editor.

        Args:
            event: Event object (optional).

        Returns:
            str: "break" to prevent further event propagation.
        """
        if self.suggestions_window:
            self.suggestions_window.destroy()
            self.suggestions_window = None
            self._suggestion_listbox = None
            self.focus_set()
        return "break"

    def show_tooltip(self, event=None):
        """
        Show tooltip with command description or diagnostic information.

        Displays contextual help when hovering over G-code commands or
        lines with parser diagnostics. Shows command descriptions from
        the definitions file and enhanced parser error/warning details.

        Args:
            event: Mouse event object (optional). Used to get cursor position.
        """
        if self.tooltip:
            self.tooltip.destroy()
        if not event or not hasattr(event, "x") or not hasattr(event, "y"):
            return
        x, y = event.x, event.y
        try:
            index = self.index(f"@{x},{y}")
            line_no = int(float(index))  # Satır numarasını al
        except Exception:
            return

        word_start = self.get(f"{index} wordstart", f"{index} wordend")

        # Enhanced parser diagnostiklerini kontrol et
        diagnostic_info = self._get_diagnostic_for_line(line_no)

        # G-code komut açıklaması veya diagnostik bilgisi göster
        if word_start in self.keywords or diagnostic_info:
            self.tooltip = tk.Toplevel()
            self.tooltip.wm_overrideredirect(True)
            frame = tk.Frame(
                self.tooltip, bg="lightyellow", borderwidth=1, relief="solid"
            )
            frame.pack(padx=5, pady=5)

            # Diagnostik bilgisi varsa önce onu göster
            if diagnostic_info:
                self._show_diagnostic_info(frame, diagnostic_info)

                # Ayırıcı çizgi
                if word_start in self.keywords:
                    separator = tk.Frame(frame, height=2, bg="gray")
                    separator.pack(fill="x", padx=5, pady=5)

            # G-code komut açıklaması göster
            if word_start in self.keywords:
                self._show_command_info(frame, word_start)

            # Tooltip'i fare pozisyonunun yanına yerleştir
            if hasattr(event, "x_root") and hasattr(event, "y_root"):
                self.tooltip.geometry(f"+{event.x_root + 15}+{event.y_root + 10}")

            # Tooltip penceresine hover efekti ekle
            def on_enter(e):
                if self.tooltip:
                    self.tooltip.attributes("-alpha", 1.0)

            def on_leave(e):
                if self.tooltip:
                    self.tooltip.attributes("-alpha", 0.9)

            frame.bind("<Enter>", on_enter)
            frame.bind("<Leave>", on_leave)

    def _get_diagnostic_for_line(self, line_no):
        """
        Get enhanced parser diagnostic information for a specific line.

        Searches the last parse result for diagnostic data associated
        with the given line number.

        Args:
            line_no (int): Line number to get diagnostics for.

        Returns:
            dict or None: Diagnostic information dictionary if found, None otherwise.
        """
        if not hasattr(self, "last_parse_result") or not self.last_parse_result:
            return None

        paths = self.last_parse_result.get("paths", [])
        for p in paths:
            if p.get("line_no") == line_no and "enhanced_diagnostic" in p:
                return p["enhanced_diagnostic"]
        return None

    def _show_diagnostic_info(self, parent_frame, diagnostic_info):
        """
        Display enhanced parser diagnostic information in tooltip.

        Creates formatted labels showing error/warning severity, category,
        message, coordinate details, and suggestions within the tooltip frame.

        Args:
            parent_frame (tk.Frame): Parent frame to add diagnostic widgets to.
            diagnostic_info (dict): Diagnostic information dictionary containing
                                   severity, category, message, suggestions, etc.
        """
        severity = diagnostic_info.get("severity", "info")
        category = diagnostic_info.get("category", "general")
        error_code = diagnostic_info.get("error_code", "")
        message = diagnostic_info.get("message", "")

        # Hata/uyarı başlığı
        severity_colors = {"error": "#ff4444", "warning": "#ff8800", "info": "#0088ff"}
        color = severity_colors.get(severity, "#666666")

        header_text = f"{severity.upper()}"
        if error_code:
            header_text += f" [{error_code}]"
        if category:
            header_text += f" - {category.title()}"

        header_label = tk.Label(
            parent_frame,
            text=header_text,
            font=("Arial", 12, "bold"),
            bg="lightyellow",
            fg=color,
            anchor="w",
        )
        header_label.pack(fill="x", padx=5, pady=2)

        # Mesaj
        if message:
            message_label = tk.Label(
                parent_frame,
                text=message,
                font=("Arial", 11),
                bg="lightyellow",
                wraplength=400,
                justify="left",
                anchor="w",
            )
            message_label.pack(fill="x", padx=5, pady=1)

        # Koordinat detayları (varsa)
        if "axis" in diagnostic_info and "value" in diagnostic_info:
            axis = diagnostic_info["axis"]
            value = diagnostic_info["value"]
            threshold = diagnostic_info.get("threshold")

            detail_text = f"Eksen: {axis}, Değer: {value:.3f}"
            if threshold:
                detail_text += f", Sınır: ±{threshold:.0f}"

            detail_label = tk.Label(
                parent_frame,
                text=detail_text,
                font=("Consolas", 10),
                bg="white",
                fg="darkred",
                anchor="w",
            )
            detail_label.pack(fill="x", padx=5, pady=1)

        # Öneriler (varsa)
        suggestions = diagnostic_info.get("suggestions", [])
        if suggestions:
            suggest_label = tk.Label(
                parent_frame,
                text="Öneriler:",
                font=("Arial", 10, "bold"),
                bg="lightyellow",
                anchor="w",
            )
            suggest_label.pack(fill="x", padx=5, pady=(5, 1))

            for suggestion in suggestions[:3]:  # En fazla 3 öneri göster
                suggest_item = tk.Label(
                    parent_frame,
                    text=f"• {suggestion}",
                    font=("Arial", 10),
                    bg="lightyellow",
                    wraplength=380,
                    justify="left",
                    anchor="w",
                )
                suggest_item.pack(fill="x", padx=10, pady=1)

    def _show_command_info(self, parent_frame, command):
        """
        Display G-code command information in tooltip.

        Shows the command name and its description, with code examples
        formatted differently from regular description text.

        Args:
            parent_frame (tk.Frame): Parent frame to add command info widgets to.
            command (str): G-code command key to display information for.
        """
        command_label = tk.Label(
            parent_frame,
            text=command,
            font=("Arial", 14, "bold"),
            bg="lightyellow",
            anchor="w",
        )
        command_label.pack(fill="x", padx=5, pady=2)

        desc_text = self.keywords[command]
        desc_parts = desc_text.split("**")
        for i, part in enumerate(desc_parts):
            if i % 2 == 1:
                example_label = tk.Label(
                    parent_frame,
                    text=part,
                    font=("Consolas", 14),
                    bg="white",
                    fg="darkblue",
                    pady=2,
                    anchor="w",
                )
                example_label.pack(fill="x", padx=5)
            else:
                if part.strip():
                    desc_label = tk.Label(
                        parent_frame,
                        text=part,
                        font=("Arial", 14),
                        bg="lightyellow",
                        wraplength=400,
                        justify="left",
                        anchor="w",
                    )
                    desc_label.pack(fill="x", padx=5)

    def force_suggestions(self, event=None):
        """
        Force display suggestions window using Ctrl+Space.

        Shows all G-code commands that start with the current word fragment,
        regardless of length. Provides manual trigger for auto-completion.

        Args:
            event: Keyboard event object (optional).

        Returns:
            str: "break" to prevent further event propagation.
        """
        current_word = self.get_current_word()
        suggestions = [
            k
            for k in self.keywords.keys()
            if k.lower().startswith(current_word.lower())
        ]
        if suggestions:
            self.show_suggestions_window(suggestions)
        return "break"

    def cut(self, event=None):
        """
        Perform cut operation.

        Generates the standard Cut event to copy selected text to clipboard
        and remove it from the editor.

        Args:
            event: Event object (optional).

        Returns:
            str: "break" to prevent further event propagation.
        """
        self.event_generate("<<Cut>>")
        return "break"

    def copy(self, event=None):
        """
        Perform copy operation.

        Generates the standard Copy event to copy selected text to clipboard.

        Args:
            event: Event object (optional).

        Returns:
            str: "break" to prevent further event propagation.
        """
        self.event_generate("<<Copy>>")
        return "break"

    def paste(self, event=None):
        """
        Perform paste operation.

        Generates the standard Paste event to insert clipboard content at cursor.
        Automatically adds undo separator for grouping.

        Args:
            event: Event object (optional).

        Returns:
            str: "break" to prevent further event propagation.
        """
        self.event_generate("<<Paste>>")
        return "break"

    # === Undo/Redo API ===
    def enable_undo(self, max_undo: int = 1000):
        """
        Enable built-in undo functionality and set maximum undo levels.

        Configures the Text widget's undo system with specified limit.
        Enables intelligent grouping of edit operations.

        Args:
            max_undo (int): Maximum number of undo operations to store. Defaults to 1000.
        """
        self.undo_enabled = True
        self.max_undo = max_undo
        try:
            self.configure(undo=True)
            self.configure(maxundo=self.max_undo)
        except Exception:
            pass

    def disable_undo(self):
        """
        Disable undo functionality.

        Turns off the Text widget's undo system and clears undo state.
        """
        self.undo_enabled = False
        try:
            self.configure(undo=False)
        except Exception:
            pass

    def undo(self) -> bool:
        """
        Perform one undo operation.

        Reverts the last edit action in the undo stack.

        Returns:
            bool: True if undo was successful, False if no undo available.
        """
        try:
            self.edit_undo()
            return True
        except Exception:
            return False

    def redo(self) -> bool:
        """
        Perform one redo operation.

        Reapplies the last undone action from the redo stack.

        Returns:
            bool: True if redo was successful, False if no redo available.
        """
        try:
            self.edit_redo()
            return True
        except Exception:
            return False

    def add_undo_separator(self):
        """
        Add separator to undo stack for grouping.

        Creates a boundary in the undo history to group related edits.
        Used for intelligent undo/redo behavior.
        """
        try:
            self.edit_separator()
        except Exception:
            pass

    def clear_history(self):
        """
        Clear the entire undo/redo history.

        Resets the edit stack, removing all stored undo and redo operations.
        """
        try:
            self.edit_reset()
        except Exception:
            pass

    # === Internal helpers ===
    def _on_undo(self, event=None):
        """
        Internal handler for undo keyboard shortcuts.

        Handles Ctrl+Z and Command+Z key combinations to trigger undo.

        Args:
            event: Keyboard event object (optional).

        Returns:
            str: "break" to prevent further event propagation.
        """

    def _on_redo(self, event=None):
        """
        Internal handler for redo keyboard shortcuts.

        Handles Ctrl+Y, Ctrl+Shift+Z, and Shift+Command+Z key combinations
        to trigger redo.

        Args:
            event: Keyboard event object (optional).

        Returns:
            str: "break" to prevent further event propagation.
        """

    def _on_paste(self, event=None):
        """
        Internal handler for paste operations.

        Adds undo separator after paste to group the pasted content
        as a single operation and marks the edit timestamp.

        Args:
            event: Paste event object (optional).
        """

    def _on_focus_out(self, event=None):
        """
        Internal handler for focus loss events.

        Adds undo separator when editor loses focus to create a boundary
        between editing sessions.

        Args:
            event: Focus out event object (optional).
        """

    def _mark_edited(self):
        """
        Mark the current time as an edit operation.

        Updates the last edit timestamp and starts the edit timer
        for intelligent undo grouping.
        """

    def _tick_edit_timer(self):
        """
        Manage the edit timer for intelligent undo grouping.

        Cancels any existing timer and schedules a new check. If the time
        since the last edit exceeds the group threshold, adds an undo
        separator to create a grouping boundary.
        """

    def handle_keypress(self, event):
        """
        Handle key press events for special behaviors.

        Processes G-code letters to auto-capitalize them, handles suggestion
        window navigation, and marks edit timestamps for undo grouping.

        Args:
            event: Keyboard event object containing pressed key information.

        Returns:
            str or None: "break" for handled special keys, None for default behavior.
        """
        char = event.char.lower()
        if char in self.gcode_letters:
            # Mevcut pozisyona büyük harfi ekle
            self.insert("insert", event.char.upper())
            # Son eklenen karakteri etiketle
            self.tag_add("gcode_letter", "insert-1c", "insert")
            return "break"
        elif self.suggestions_window:
            if event.keysym in ("Up", "Down"):
                return self.navigate_suggestions(event)
            elif event.keysym in ("Return", "Tab"):
                return self.apply_selected_suggestion(event)
            elif event.keysym == "Escape":
                return self.close_suggestions()
        # Düzenleme zaman damgasını güncelle
        self._mark_edited()
        return None

    def insert(self, index, chars, *args):
        """
        Override Text widget insert method with G-code letter processing.

        Automatically capitalizes G-code letters, adds undo separators for
        multi-character inserts, applies syntax highlighting, and updates
        edit timestamps for grouping.

        Args:
            index: Position index where text should be inserted.
            chars: Text string to insert.
            *args: Additional arguments passed to parent insert method.
        """
        # Uzun metin eklemelerinde (>=2 karakter) ayrı bir undo bloğu başlat
        try:
            if isinstance(chars, str) and len(chars) > 1:
                self.edit_separator()
        except Exception:
            pass

        # G-code harflerini kontrol et ve büyük harfe çevirerek tek seferde ekle
        transformed = "".join(
            (c.upper() if c.lower() in self.gcode_letters else c) for c in chars
        )
        start_index = self.index(index)
        super().insert(index, transformed, *args)

        # Eklenen bölümde G-code harflerini etiketle
        for offset, ch in enumerate(transformed):
            if ch.lower() in self.gcode_letters:
                start = f"{start_index}+{offset}c"
                end = f"{start_index}+{offset + 1}c"
                self.tag_add("gcode_letter", start, end)

        # Programatik eklemeden sonra düzenleme zamanını güncelle
        self._mark_edited()

    def handle_keyrelease(self, event=None):
        """
        Handle key release events for auto-completion.

        Triggers line highlighting and auto-completion suggestions
        when non-whitespace characters are released.

        Args:
            event: Keyboard event object (optional).
        """
        if event and hasattr(event, "char") and event.char and not event.char.isspace():
            self.highlight_current_line()
            self.show_suggestions(event)

    def handle_space(self, event=None):
        """
        Handle space key press events.

        Triggers current line highlighting when space is pressed.

        Args:
            event: Keyboard event object (optional).

        Returns:
            None: Allows default space key behavior.
        """
        self.highlight_current_line()
        return None

    def handle_return(self, event=None):
        """
        Handle Enter key press events.

        Applies selected suggestion if window is open, otherwise adds
        undo separator and highlights current line.

        Args:
            event: Keyboard event object (optional).

        Returns:
            str or None: "break" if suggestion was applied, None for default behavior.
        """
        if self.suggestions_window:
            self.apply_selected_suggestion(event)
            return "break"
        # Enter basımı bir gruplama sınırı olsun
        self.add_undo_separator()
        self.highlight_current_line()
        return None

    def clear_diagnostics(self):
        """
        Clear all error and warning line highlights.

        Removes error_line and warning_line tags from the entire text
        to reset diagnostic highlighting.
        """
        self.tag_remove("error_line", "1.0", tk.END)
        self.tag_remove("warning_line", "1.0", tk.END)

    def annotate_parse_result(self, result):
        """
        Annotate editor with parser error and warning highlights.

        Processes parse result to highlight lines with errors or warnings.
        Supports enhanced parser diagnostic structure with detailed error
        information, coordinate warnings, and suggestions.

        Args:
            result (dict): Parser output containing 'paths' and 'layers' data.
                          Each path may contain diagnostic information.

        Returns:
            dict: Summary with counts of errors and warnings found.
                 Format: {'errors': int, 'warnings': int}
        """
        self.clear_diagnostics()

        # Parse sonucunu tooltip için sakla
        self.last_parse_result = result
        errors = 0
        warnings = 0
        if not isinstance(result, dict):
            return {"errors": 0, "warnings": 0}

        paths = result.get("paths") or []
        for p in paths:
            ptype = p.get("type")
            line_no = p.get("line_no")
            if not line_no or not isinstance(line_no, int):
                continue

            start = f"{line_no}.0"
            end = f"{line_no}.end"

            # Enhanced parser'ın yeni diagnostik yapısını destekle
            if ptype == "parse_error":
                self.tag_add("error_line", start, end)
                errors += 1

                # Enhanced diagnostik bilgisi varsa tooltip için kaydet
                if "diagnostic" in p:
                    diagnostic = p["diagnostic"]
                    severity = diagnostic.get("severity", "error")
                    category = diagnostic.get("category", "syntax")
                    error_code = diagnostic.get("error_code", "E001")

                    # Diagnostik bilgisini path'e ekle (tooltip için)
                    p["enhanced_diagnostic"] = {
                        "severity": severity,
                        "category": category,
                        "error_code": error_code,
                        "suggestions": diagnostic.get("suggestions", []),
                    }

            elif ptype in ("unsupported", "unknown_param"):
                self.tag_add("warning_line", start, end)
                warnings += 1

                # Uyarı seviyesini kontrol et
                if "diagnostic" in p:
                    diagnostic = p["diagnostic"]
                    severity = diagnostic.get("severity", "warning")

                    # Kritik uyarıları hata olarak işaretle
                    if severity == "error":
                        self.tag_remove("warning_line", start, end)
                        self.tag_add("error_line", start, end)
                        warnings -= 1
                        errors += 1

            elif ptype == "warning":
                # Yeni warning tipi için destek
                self.tag_add("warning_line", start, end)
                warnings += 1

                # Koordinat uyarıları için özel işleme
                if "coordinate_warnings" in p:
                    coord_warnings = p["coordinate_warnings"]
                    if len(coord_warnings) > 0:
                        # İlk koordinat uyarısının bilgisini kaydet
                        first_warning = coord_warnings[0]
                        p["enhanced_diagnostic"] = {
                            "severity": "warning",
                            "category": "coordinate",
                            "error_code": "W001",
                            "message": first_warning.get(
                                "message", "Koordinat değeri normal sınırları aşıyor"
                            ),
                            "axis": first_warning.get("axis"),
                            "value": first_warning.get("value"),
                            "threshold": first_warning.get("threshold"),
                        }

        # Son durum hafızada tutulsun (isteğe bağlı)
        self.last_diagnostics = {"errors": errors, "warnings": warnings}
        return self.last_diagnostics

    def highlight_current_line(self):
        """
        Highlight G-code letters in the current line.

        Clears existing gcode_letter tags from the current line and
        reapplies them to all G-code parameter letters (G, X, Y, Z, M, etc.).
        Provides real-time syntax highlighting as the user types.
        """
        # Mevcut satırı al
        current_line = self.get("insert linestart", "insert lineend")

        # Satırdaki etiketleri temizle
        self.tag_remove("gcode_letter", "insert linestart", "insert lineend")

        # G-code harflerini bul ve etiketle
        pos = 0
        for char in current_line:
            if char.lower() in self.gcode_letters:
                start = f"insert linestart+{pos}c"
                end = f"insert linestart+{pos + 1}c"
                self.tag_add("gcode_letter", start, end)
            pos += 1

    def highlight_all_text(self):
        """
        Highlight G-code letters throughout the entire text.

        Scans the complete editor content and applies gcode_letter tags
        to all G-code parameter letters. Used for initial syntax highlighting
        when loading files or refreshing the display.
        """
        content = self.get("1.0", tk.END)
        for i, char in enumerate(content):
            if char.lower() in self.gcode_letters:
                start = f"1.0+{i}c"
                end = f"1.0+{i + 1}c"
                self.tag_add("gcode_letter", start, end)


def create_text_editor(root):
    """
    Create and return an enhanced G-code editor widget.

    Factory function that creates an EditorFrame containing a fully
    configured GCodeEditor with all features enabled including line
    numbers, auto-completion, syntax highlighting, and undo/redo.

    Args:
        root: Tkinter root window or parent frame to contain the editor.

    Returns:
        EditorFrame: Frame widget containing the configured G-code editor.
                     Use get_editor() method to access the actual GCodeEditor.
    """
    frame = EditorFrame(root, wrap=tk.NONE, undo=True)
    return frame
