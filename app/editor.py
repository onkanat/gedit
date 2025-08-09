import tkinter as tk
from tkinter import ttk
import re
import json
import os

class LineNumbers(tk.Canvas):
    """
    Satır numaralarını gösteren canvas.
    Text widget'ı ile entegre çalışır ve editördeki satır numaralarını gösterir.
    """
    def __init__(self, parent, text_widget, *args, **kwargs):
        super().__init__(parent, width=30, *args, **kwargs)
        self.text_widget = text_widget
        self.redraw()  # İlk çizim
        
        # Text widget'ın scroll ve değişiklik olaylarını dinle
        # Sadece gerekli olaylarda redraw çağrılır (performans için throttle)
        self.text_widget.bind('<KeyRelease>', self.redraw)
        self.text_widget.bind('<MouseWheel>', self.redraw)
        self.text_widget.bind('<Configure>', self.redraw)

    def redraw(self, *args):
        """
        Satır numaralarını yeniden çizer.
        Text widget'ın görünür alanına göre günceller.
        """
        self.delete('all')  # Canvas'ı temizle
        
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
                    y,   # Y koordinatı
                    text=str(line_num),
                    anchor='n',
                    fill='gray50',
                    font=self.text_widget['font']
                )
        
        self.after(10, self.redraw)  # Periyodik güncelleme

class EditorFrame(tk.Frame):
    """
    Editör frame'ini saran ana sınıf.
    GCodeEditor widget'ını içerir ve dışarıya erişim sağlar.
    """
    def __init__(self, master=None, **kwargs):
        super().__init__(master)
        self.editor = GCodeEditor(self, **kwargs)
        
    def get_editor(self):
        """
        Editör örneğini döndürür.
        :return: GCodeEditor instance
        """
        return self.editor

class GCodeEditor(tk.Text):
    """
    G-code için özelleştirilmiş gelişmiş bir Tkinter Text widget'ı.
    Otomatik tamamlama, satır numarası, tooltip ve sözdizimi vurgulama içerir.
    """
    def __init__(self, master=None, **kwargs):
        # Varsayılan font ayarı
        if 'font' not in kwargs:
            kwargs['font'] = ('Courier', 14)

        # Text widget'ı oluştur
        super().__init__(master, **kwargs)

        # Scrollbar ve line numbers
        self.scrollbar = ttk.Scrollbar(master, orient='vertical', command=self.yview)
        self.configure(yscrollcommand=self.scrollbar.set)
        self.line_numbers = LineNumbers(master, self, bg='#f0f0f0')

        # Widget'ları yerleştir
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        self.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Diğer başlangıç ayarları
        self.suggestions_window = None
        self._suggestion_listbox = None
        self.tooltip = None

        # G-code tanımlarını JSON dosyasından yükle (global cache)
        if not hasattr(GCodeEditor, '_gcode_keywords_cache'):
            GCodeEditor._gcode_keywords_cache = self.load_gcode_definitions()
        self.keywords = GCodeEditor._gcode_keywords_cache

        # Text tag'leri oluştur
        self.tag_configure("gcode_letter", foreground="blue", font=(kwargs['font'][0], kwargs['font'][1], "bold"))
        # Diagnostik etiketleri (hata/uyarı satır vurguları)
        self.tag_configure("error_line", background="#ffefef")
        self.tag_configure("warning_line", background="#fff9db")

        # Event bindings
        self.bind('<KeyPress>', self.handle_keypress)
        self.bind('<KeyRelease>', self.show_suggestions)
        self.bind('<Control-space>', self.force_suggestions)
        self.bind('<Button-1>', self.handle_click)
        self.bind('<Control-x>', self.cut)
        self.bind('<Control-c>', self.copy)
        self.bind('<Control-v>', self.paste)
        self.bind('<Motion>', self.show_tooltip)
        # Enter/Tab özel davranışları
        self.bind('<Return>', self.handle_return)
        self.bind('<Tab>', self.handle_tab)

        # G-code harfleri listesi
        self.gcode_letters = {'g', 'x', 'y', 'z', 'm', 'i', 'j', 'k', 'f', 'r', 's', 't', 'n'}

    def load_gcode_definitions(self):
        """
        G-code tanımlarını JSON dosyasından yükler.
        :return: dict, G-code anahtarları ve açıklamaları
        """
        try:
            # Dosya yolunu belirle
            json_path = os.path.join(os.path.dirname(__file__), 'data', 'gcode_definitions.json')
            
            # JSON dosyasını oku
            with open(json_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except Exception as e:
            print(f"G-code tanımları yüklenemedi: {e}")
            # Hata durumunda varsayılan boş sözlük döndür
            return {}

    def get_current_word(self):
        """
        İmleç pozisyonundaki kelimeyi döndürür.
        :return: str, mevcut kelime
        """
        current_line = self.get("insert linestart", "insert")
        match = re.search(r'[A-Za-z0-9]*$', current_line)
        return match.group(0) if match else ''

    def show_suggestions(self, event=None):
        """
        Otomatik tamamlama önerilerini gösterir.
        :param event: Klavye olayı (isteğe bağlı)
        """
        # Sadece harf veya silme tuşlarında tetiklenir
        if event and not (event.char.isalpha() or event.keysym in ['space', 'BackSpace']):
            return
        current_word = self.get_current_word()
        if len(current_word) >= 1:
            # startswith yerine substring eşleşme (daha akıllı)
            suggestions = [k for k in self.keywords.keys() if current_word.lower() in k.lower()]
            if suggestions:
                self.show_suggestions_window(suggestions)
            elif self.suggestions_window:
                self.close_suggestions()
        elif self.suggestions_window:
            self.close_suggestions()

    def show_suggestions_window(self, suggestions):
        """
        Otomatik tamamlama öneri penceresini gösterir veya günceller.
        :param suggestions: list, öneri anahtarları
        """
        # Pencere zaten varsa sadece güncelle
        if self.suggestions_window and self.suggestions_window.winfo_exists() and self._suggestion_listbox:
            listbox = self._suggestion_listbox
            listbox.delete(0, tk.END)
            for suggestion in suggestions:
                display_text = f"{suggestion} - {self.keywords[suggestion]}"
                listbox.insert(tk.END, display_text)
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

        listbox = tk.Listbox(self.suggestions_window,
                             selectmode=tk.SINGLE,
                             activestyle='none',
                             height=min(len(suggestions), 10),
                             width=max(40, max(len(f"{s} - {self.keywords[s]}") for s in suggestions)),
                             font=self['font'])
        listbox.pack(fill=tk.BOTH, expand=True)
        for suggestion in suggestions:
            display_text = f"{suggestion} - {self.keywords[suggestion]}"
            listbox.insert(tk.END, display_text)
        if listbox.size() > 0:
            listbox.selection_set(0)
            listbox.see(0)
        self._suggestion_listbox = listbox
        self.suggestions_window.geometry(f"+{x}+{y}")
        listbox.bind('<Double-Button-1>', self.apply_selected_suggestion)
        listbox.bind('<Return>', self.apply_selected_suggestion)
        listbox.bind('<Escape>', self.close_suggestions)
        listbox.bind('<FocusOut>', lambda e: self.after(100, self.close_suggestions))
        self.suggestions_window.update_idletasks()
        self.suggestions_window.lift()
        self.focus_set()
        listbox.activate(0)
        self.suggestions_window.update()

    def navigate_suggestions(self, event):
        """
        Ok tuşları ile öneriler arasında gezinmeyi sağlar.
        :param event: Klavye olayı
        """
        if not self.suggestions_window or not self._suggestion_listbox:
            return "break"
        listbox = self._suggestion_listbox
        current = listbox.curselection()
        if event.keysym == 'Up' and current and current[0] > 0:
            listbox.selection_clear(current)
            new_index = current[0] - 1
            listbox.selection_set(new_index)
            listbox.see(new_index)
        elif event.keysym == 'Down' and current and current[0] < listbox.size() - 1:
            listbox.selection_clear(current)
            new_index = current[0] + 1
            listbox.selection_set(new_index)
            listbox.see(new_index)
        return "break"

    

    def handle_tab(self, event=None):
        """
        Tab tuşuna basıldığında öneri uygular veya normal davranışı sürdürür.
        :param event: Klavye olayı (isteğe bağlı)
        """
        if self.suggestions_window:
            self.apply_selected_suggestion(event)
            return "break"
        return None

    def handle_click(self, event=None):
        """
        Editöre tıklandığında öneri penceresini kapatır.
        :param event: Mouse olayı (isteğe bağlı)
        """
        if self.suggestions_window and self._suggestion_listbox:
            # Tıklama öneri penceresinde değilse kapat
            if not (event and hasattr(event, 'widget') and event.widget == self._suggestion_listbox):
                self.close_suggestions()

    def apply_selected_suggestion(self, event=None):
        """
        Seçili öneriyi editöre uygular.
        :param event: Klavye veya mouse olayı (isteğe bağlı)
        """
        if not self.suggestions_window or not self._suggestion_listbox:
            return "break"
        listbox = self._suggestion_listbox
        selection = listbox.curselection()
        if selection:
            suggestion = listbox.get(selection[0]).split(' - ')[0]
            current_word = self.get_current_word()
            if current_word:
                position = "insert-{}c".format(len(current_word))
                self.delete(position, "insert")
            self.insert("insert", suggestion + ' ')
            self.close_suggestions()
            self.see(tk.INSERT)
            self.focus_set()
        return "break"

    def close_suggestions(self, event=None):
        """
        Otomatik tamamlama öneri penceresini kapatır.
        :param event: Olay (isteğe bağlı)
        """
        if self.suggestions_window:
            self.suggestions_window.destroy()
            self.suggestions_window = None
            self._suggestion_listbox = None
            self.focus_set()
        return "break"

    def show_tooltip(self, event=None):
        """
        İmleçteki kelime için tooltip (ipucu) gösterir.
        :param event: Mouse olayı (isteğe bağlı)
        """
        if self.tooltip:
            self.tooltip.destroy()
        if not event or not hasattr(event, 'x') or not hasattr(event, 'y'):
            return
        x, y = event.x, event.y
        try:
            index = self.index(f"@{x},{y}")
        except Exception:
            return
        word_start = self.get(f"{index} wordstart", f"{index} wordend")
        if word_start in self.keywords:
            self.tooltip = tk.Toplevel()
            self.tooltip.wm_overrideredirect(True)
            frame = tk.Frame(self.tooltip, bg="lightyellow", borderwidth=1, relief="solid")
            frame.pack(padx=5, pady=5)
            command_label = tk.Label(frame, 
                                   text=word_start,
                                   font=("Arial", 14, "bold"),
                                   bg="lightyellow",
                                   anchor="w")
            command_label.pack(fill="x", padx=5, pady=2)
            desc_text = self.keywords[word_start]
            desc_parts = desc_text.split("**")
            for i, part in enumerate(desc_parts):
                if i % 2 == 1:
                    example_label = tk.Label(frame,
                                          text=part,
                                          font=("Consolas", 14),
                                          bg="white",
                                          fg="darkblue",
                                          pady=2,
                                          anchor="w")
                    example_label.pack(fill="x", padx=5)
                else:
                    if part.strip():
                        desc_label = tk.Label(frame,
                                            text=part,
                                            font=("Arial", 14),
                                            bg="lightyellow",
                                            wraplength=400,
                                            justify="left",
                                            anchor="w")
                        desc_label.pack(fill="x", padx=5)
            # Tooltip'i fare pozisyonunun yanına yerleştir
            if hasattr(event, 'x_root') and hasattr(event, 'y_root'):
                self.tooltip.geometry(f"+{event.x_root+15}+{event.y_root+10}")
            # Tooltip penceresine hover efekti ekle
            def on_enter(e):
                if self.tooltip:
                    self.tooltip.attributes('-alpha', 1.0)
            def on_leave(e):
                if self.tooltip:
                    self.tooltip.attributes('-alpha', 0.9)
            frame.bind('<Enter>', on_enter)
            frame.bind('<Leave>', on_leave)

    def force_suggestions(self, event=None):
        """
        Ctrl+Space ile öneri penceresini zorla gösterir.
        :param event: Klavye olayı (isteğe bağlı)
        """
        current_word = self.get_current_word()
        suggestions = [k for k in self.keywords.keys() 
                      if k.lower().startswith(current_word.lower())]
        if suggestions:
            self.show_suggestions_window(suggestions)
        return "break"

    def cut(self, event=None):
        """
        Kesme işlemini gerçekleştirir.
        :param event: Olay (isteğe bağlı)
        """
        self.event_generate("<<Cut>>")
        return "break"

    def copy(self, event=None):
        """
        Kopyalama işlemini gerçekleştirir.
        :param event: Olay (isteğe bağlı)
        """
        self.event_generate("<<Copy>>")
        return "break"

    def paste(self, event=None):
        """
        Yapıştırma işlemini gerçekleştirir.
        :param event: Olay (isteğe bağlı)
        """
        self.event_generate("<<Paste>>")
        return "break"

    def handle_keypress(self, event):
        """
        Tuş basımlarını yönetir, G-code harflerini işler.
        :param event: Klavye olayı
        """
        char = event.char.lower()
        if char in self.gcode_letters:
            # Mevcut pozisyona büyük harfi ekle
            self.insert("insert", event.char.upper())
            # Son eklenen karakteri etiketle
            self.tag_add("gcode_letter", "insert-1c", "insert")
            return "break"
        elif self.suggestions_window:
            if event.keysym in ('Up', 'Down'):
                return self.navigate_suggestions(event)
            elif event.keysym in ('Return', 'Tab'):
                return self.apply_selected_suggestion(event)
            elif event.keysym == 'Escape':
                return self.close_suggestions()
        return None

    def insert(self, index, chars, *args):
        """
        Text widget insert metodunu override eder, G-code harflerini büyük harfe çevirir.
        :param index: Ekleme konumu
        :param chars: Eklenecek karakterler
        """
        # G-code harflerini kontrol et ve büyük harfe çevir
        new_chars = ''
        for char in chars:
            if char.lower() in self.gcode_letters:
                new_chars += char.upper()
                # Insert pozisyonunu hesapla
                pos = self.index(index)
                # Karakteri ekle ve etiketle
                super().insert(index, char.upper(), *args)
                self.tag_add("gcode_letter", pos, f"{pos}+1c")
                index = f"{pos}+1c"
            else:
                new_chars += char
                super().insert(index, char, *args)
                index = f"{self.index(index)}+1c"

    def handle_keyrelease(self, event=None):
        """
        Tuş bırakıldığında çalışır, otomatik tamamlama tetikleyebilir.
        :param event: Klavye olayı (isteğe bağlı)
        """
        if event and hasattr(event, 'char') and event.char and not event.char.isspace():
            self.highlight_current_line()
            self.show_suggestions(event)

    def handle_space(self, event=None):
        """
        Boşluk tuşuna basıldığında çalışır, satırı vurgular.
        :param event: Klavye olayı (isteğe bağlı)
        """
        self.highlight_current_line()
        return None

    def handle_return(self, event=None):
        """
        Enter tuşuna basıldığında çalışır, satırı vurgular ve öneri uygular.
        :param event: Klavye olayı (isteğe bağlı)
        """
        if self.suggestions_window:
            self.apply_selected_suggestion(event)
            return "break"
        self.highlight_current_line()
        return None

    def clear_diagnostics(self):
        """Tüm hata/uyarı vurgularını temizler."""
        self.tag_remove("error_line", "1.0", tk.END)
        self.tag_remove("warning_line", "1.0", tk.END)

    def annotate_parse_result(self, result):
        """
        parse_gcode çıktısına göre satırları hata/uyarı olarak vurgular.
        :param result: dict, {'paths': [...], 'layers': [...]}
        :return: dict, {'errors': int, 'warnings': int}
        """
        self.clear_diagnostics()
        errors = 0
        warnings = 0
        if not isinstance(result, dict):
            return {'errors': 0, 'warnings': 0}
        paths = result.get('paths') or []
        for p in paths:
            ptype = p.get('type')
            line_no = p.get('line_no')
            if not line_no or not isinstance(line_no, int):
                continue
            start = f"{line_no}.0"
            end = f"{line_no}.end"
            if ptype in ('parse_error',):
                self.tag_add("error_line", start, end)
                errors += 1
            elif ptype in ('unsupported', 'unknown_param'):
                self.tag_add("warning_line", start, end)
                warnings += 1
        # Son durum hafızada tutulsun (isteğe bağlı)
        self.last_diagnostics = {'errors': errors, 'warnings': warnings}
        return self.last_diagnostics

    def highlight_current_line(self):
        """
        Mevcut satırı vurgular.
        """
        """Mevcut satırdaki G-code harflerini vurgula"""
        # Mevcut satırı al
        current_line = self.get("insert linestart", "insert lineend")
        
        # Satırdaki etiketleri temizle
        self.tag_remove("gcode_letter", "insert linestart", "insert lineend")
        
        # G-code harflerini bul ve etiketle
        pos = 0
        for char in current_line:
            if char.lower() in self.gcode_letters:
                start = f"insert linestart+{pos}c"
                end = f"insert linestart+{pos+1}c"
                self.tag_add("gcode_letter", start, end)
            pos += 1

    def highlight_all_text(self):
        """
        Tüm metni vurgular.
        """
        """Tüm metindeki G-code harflerini vurgula"""
        content = self.get("1.0", tk.END)
        for i, char in enumerate(content):
            if char.lower() in self.gcode_letters:
                start = f"1.0+{i}c"
                end = f"1.0+{i+1}c"
                self.tag_add("gcode_letter", start, end)

def create_text_editor(root):
    """
    Gelişmiş G-code editörünü oluşturur ve döndürür.
    :param root: Tkinter ana pencere veya frame
    :return: EditorFrame instance
    """
    frame = EditorFrame(root, wrap=tk.NONE, undo=True)
    return frame
