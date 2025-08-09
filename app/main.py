import tkinter as tk
from tkinter import filedialog, messagebox
from gui import create_main_window
from editor import create_text_editor
from preview import show_preview
from gcode_parser import parse_gcode

current_file = None
editor = None  # Global editor referansı

def check_syntax():
    """
    Editördeki G-code'un sözdizimini kontrol eder.
    Hatalıysa uyarı verir, doğruysa bilgi mesajı gösterir.
    """
    """G-code sözdizimi kontrolü yapar"""
    global editor
    if editor is None:
        messagebox.showerror("Hata", "Editör başlatılamadı.")
        return
    content = editor.get("1.0", tk.END).strip()
    if not content:
        messagebox.showwarning("Uyarı", "Editör boş!")
        return
    
    try:
        # parse_gcode fonksiyonunu kullanarak sözdizimi kontrolü
        result = parse_gcode(content)
        # Editörde satırları işaretle
        diag = editor.annotate_parse_result(result) if (editor is not None and hasattr(editor, 'annotate_parse_result')) else {'errors': 0, 'warnings': 0}
        errors = diag.get('errors', 0)
        warnings = diag.get('warnings', 0)
        if errors == 0:
            if warnings:
                messagebox.showinfo("Sözdizimi", f"Hata yok, {warnings} uyarı bulundu.")
            else:
                messagebox.showinfo("Sözdizimi", "Hata ve uyarı yok.")
        else:
            messagebox.showwarning("Sözdizimi", f"{errors} hata, {warnings} uyarı bulundu. Hatalı satırlar kırmızımsı, uyarılar sarımsı renkte vurgulandı.")
    except Exception as e:
        messagebox.showerror("Hata", f"Sözdizimi hatası:\n{str(e)}")

def save_file():
    """
    Mevcut dosyayı kaydeder. Dosya yoksa save_file_as çağrılır.
    """
    """Dosyayı kaydeder"""
    global current_file, editor
    if editor is None:
        messagebox.showerror("Hata", "Editör başlatılamadı.")
        return
    if current_file:
        content = editor.get("1.0", tk.END)
        try:
            with open(current_file, 'w') as file:
                file.write(content)
            messagebox.showinfo("Başarılı", f"Dosya kaydedildi:\n{current_file}")
        except Exception as e:
            messagebox.showerror("Hata", f"Dosya kaydedilemedi:\n{str(e)}")
    else:
        save_file_as()

def save_file_as():
    """
    Dosyayı farklı kaydeder (Save As...)
    """
    """Dosyayı farklı kaydeder"""
    global current_file, editor
    file_path = filedialog.asksaveasfilename(
        defaultextension=".nc",
        filetypes=[("NC files", "*.nc"), ("All files", "*.*")],
        title="G-code Dosyasını Kaydet"
    )
    if file_path:
        current_file = file_path
        save_file()

def load_file():
    """
    Dosya açma işlemini gerçekleştirir.
    """
    """Dosya yükler"""
    global current_file, editor
    if editor is None:
        messagebox.showerror("Hata", "Editör başlatılamadı.")
        return
    file_path = filedialog.askopenfilename(
        filetypes=[("NC files", "*.nc"), ("All files", "*.*")],
        title="G-code Dosyası Aç"
    )
    if file_path:
        try:
            with open(file_path, 'r') as file:
                content = file.read()
            editor.delete("1.0", tk.END)
            editor.insert("1.0", content)
            current_file = file_path
            messagebox.showinfo("Başarılı", f"Dosya yüklendi:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Hata", f"Dosya yüklenemedi:\n{str(e)}")

def new_file():
    """
    Yeni dosya oluşturur, mevcut değişiklikleri kaydetmeyi sorar.
    """
    """Yeni dosya oluşturur"""
    global current_file, editor
    if editor is None:
        messagebox.showerror("Hata", "Editör başlatılamadı.")
        return
    if editor.get("1.0", tk.END).strip():
        if messagebox.askyesno("Kaydet", "Mevcut değişiklikler kaydedilsin mi?"):
            save_file()
    
    editor.delete("1.0", tk.END)
    current_file = None

"""
Ana uygulama başlatıcı. Tkinter ana pencereyi ve editörü başlatır.
"""
if __name__ == "__main__":
    root = tk.Tk()
    root.title("CNC G Code Editor")

    # Pencere boyutunu ayarla
    root.geometry("800x600")

    # Editor frame'i oluştur
    editor_frame = create_text_editor(root)
    editor_frame.pack(fill=tk.BOTH, expand=True)
    
    # Global editor referansını al
    editor = editor_frame.get_editor()

    menu_bar = create_main_window(root, new_file, load_file, save_file, root.quit)
    root.config(menu=menu_bar)

    button_frame = tk.Frame(root)
    button_frame.pack(pady=5)

    tk.Button(button_frame, text="Check Syntax", command=check_syntax).pack(side=tk.LEFT, padx=5)
    tk.Button(button_frame, text="Preview", command=lambda: show_preview(editor, root)).pack(side=tk.LEFT, padx=5)
    tk.Button(button_frame, text="Save As...", command=save_file_as).pack(side=tk.LEFT, padx=5)

    root.mainloop()
