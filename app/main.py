import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from gui import create_main_window
from editor import create_text_editor
from preview import show_preview
from gcode_parser import parse_gcode

current_file = None
editor = None  # Global editor referansı
problems_tree = None  # Problems panelindeki Treeview
status_var = None  # Status bar metni
last_diag = {"errors": 0, "warnings": 0}


def build_diagnostics_from_result(result):
    """parse_gcode sonucundan Problems paneli için teşhis listesi üretir."""
    diags = []
    if not isinstance(result, dict):
        return diags
    for p in result.get("paths") or []:
        ptype = p.get("type")
        line_no = p.get("line_no")
        if ptype in ("parse_error", "unsupported", "unknown_param") and isinstance(
            line_no, int
        ):
            msg = p.get("message") or p.get("raw") or ptype
            diags.append({"type": ptype, "line": line_no, "message": str(msg)})
    return diags


def clear_problems():
    """Problems panelini temizler."""
    global problems_tree
    if problems_tree is None:
        return
    for i in problems_tree.get_children():
        problems_tree.delete(i)


def populate_problems(result):
    """Problems panelini parse sonucuna göre doldurur."""
    global problems_tree
    if problems_tree is None:
        return
    clear_problems()
    for d in build_diagnostics_from_result(result):
        problems_tree.insert("", tk.END, values=(d["type"], d["line"], d["message"]))


def on_problem_double_click(event=None):
    """Problems panelindeki bir satıra çift tıklandığında ilgili satıra git."""
    global problems_tree, editor
    if problems_tree is None or editor is None:
        return
    sel = problems_tree.selection()
    if not sel:
        return
    item = problems_tree.item(sel[0])
    values = item.get("values") or []
    if len(values) < 2:
        return
    try:
        line_no = int(values[1])
    except Exception:
        return
    try:
        editor.mark_set("insert", f"{line_no}.0")
        editor.see(f"{line_no}.0")
        editor.focus_set()
    except Exception:
        pass


def update_status(errors=None, warnings=None):
    """Status bar (Ln, Col, Errors, Warnings, Lines) bilgisini günceller."""
    global editor, status_var, last_diag
    if editor is None or status_var is None:
        return
    try:
        idx = editor.index("insert")
        line_s, col_s = idx.split(".")
        line = int(line_s)
        col = int(col_s) + 1
        total_lines = int(editor.index("end-1c").split(".")[0])
    except Exception:
        line = 1
        col = 1
        total_lines = 1
    if errors is None or warnings is None:
        errors = last_diag.get("errors", 0) if errors is None else errors
        warnings = last_diag.get("warnings", 0) if warnings is None else warnings
    status_var.set(
        f"Ln {line}, Col {col}    Errors: {errors}  Warnings: {warnings}  Lines: {total_lines}"
    )


def on_editor_activity(event=None):
    """Editörde klavye/tıklama gibi hareketlerde status bar'ı güncelle."""
    update_status()


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
        diag = (
            editor.annotate_parse_result(result)
            if (editor is not None and hasattr(editor, "annotate_parse_result"))
            else {"errors": 0, "warnings": 0}
        )
        # Problems panelini doldur
        populate_problems(result)
        errors = diag.get("errors", 0)
        warnings = diag.get("warnings", 0)
        # Son teşhisleri kaydet ve status bar'ı güncelle
        global last_diag
        last_diag = {"errors": errors, "warnings": warnings}
        update_status(errors=errors, warnings=warnings)
        if errors == 0:
            if warnings:
                messagebox.showinfo("Sözdizimi", f"Hata yok, {warnings} uyarı bulundu.")
            else:
                messagebox.showinfo("Sözdizimi", "Hata ve uyarı yok.")
        else:
            messagebox.showwarning(
                "Sözdizimi",
                f"{errors} hata, {warnings} uyarı bulundu. Hatalı satırlar kırmızımsı, uyarılar sarımsı renkte vurgulandı.",
            )
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
            with open(current_file, "w") as file:
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
        title="G-code Dosyasını Kaydet",
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
        title="G-code Dosyası Aç",
    )
    if file_path:
        try:
            with open(file_path, "r") as file:
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

    tk.Button(button_frame, text="Check Syntax", command=check_syntax).pack(
        side=tk.LEFT, padx=5
    )
    tk.Button(
        button_frame, text="Preview", command=lambda: show_preview(editor, root)
    ).pack(side=tk.LEFT, padx=5)
    tk.Button(button_frame, text="Save As...", command=save_file_as).pack(
        side=tk.LEFT, padx=5
    )

    # Problems paneli
    problems_frame = tk.Frame(root)
    problems_frame.pack(fill=tk.BOTH, expand=False, padx=5, pady=(0, 0))
    columns = ("type", "line", "message")
    problems_tree = ttk.Treeview(
        problems_frame, columns=columns, show="headings", height=6
    )
    problems_tree.heading("type", text="Type")
    problems_tree.heading("line", text="Line")
    problems_tree.heading("message", text="Message")
    problems_tree.column("type", width=120, anchor=tk.W)
    problems_tree.column("line", width=60, anchor=tk.CENTER)
    problems_tree.column("message", width=600, anchor=tk.W)
    yscroll = ttk.Scrollbar(
        problems_frame, orient="vertical", command=problems_tree.yview
    )
    problems_tree.configure(yscrollcommand=yscroll.set)
    problems_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    yscroll.pack(side=tk.RIGHT, fill=tk.Y)
    problems_tree.bind("<Double-1>", on_problem_double_click)

    # Status bar (en alt)
    status_frame = tk.Frame(root)
    status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=5)
    status_label = tk.Label(status_frame, anchor=tk.W)
    status_label.pack(fill=tk.X)
    status_var = tk.StringVar()
    status_label.configure(textvariable=status_var)

    # Editör etkinliklerine status güncellemesi bağla
    editor.bind("<KeyRelease>", on_editor_activity, add=True)
    editor.bind("<Button-1>", on_editor_activity, add=True)
    update_status()

    root.mainloop()
