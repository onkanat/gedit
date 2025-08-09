import tkinter as tk
from gcode_parser import parse_gcode
import math  # math modülünü ekle
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

def show_preview(editor, root):
    """
    G-code önizleme penceresini açar. 2D ve 3D görselleştirme sunar.
    :param editor: GCodeEditor instance
    :param root: Tkinter ana pencere
    """
    """G-code önizleme penceresini gösterir."""
    code = editor.get("1.0", tk.END)
    gcode_result = parse_gcode(code)
    paths = gcode_result['paths'] if isinstance(gcode_result, dict) and 'paths' in gcode_result else gcode_result
    
    # Mevcut önizleme pencerelerini kapat
    for widget in root.winfo_children():
        if isinstance(widget, tk.Toplevel) and widget.title() in ["G-code Preview", "3D Preview"]:
            widget.destroy()

    # 2D ve 3D preview pencerelerini oluştur
    preview_window_2d = tk.Toplevel(root)
    preview_window_2d.title("G-code Preview")
    preview_window_3d = tk.Toplevel(root)
    preview_window_3d.title("3D Preview")

    # 2D kontrol çubuğu ve canvas
    ctrl_frame = tk.Frame(preview_window_2d)
    ctrl_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
    tk.Label(ctrl_frame, text="2D Düzlem:").pack(side=tk.LEFT)
    plane_var = tk.StringVar(value="Auto")
    plane_options = ["Auto", "G17 (XY)", "G18 (XZ)", "G19 (YZ)"]
    tk.OptionMenu(ctrl_frame, plane_var, *plane_options).pack(side=tk.LEFT, padx=8)

    canvas_2d = tk.Canvas(preview_window_2d, width=600, height=400, bg="white")
    canvas_2d.pack(padx=10, pady=10)

    def draw_grid(axis_labels=("X","Y")):
        canvas_2d.delete("grid")
        grid_spacing = 50
        for y in range(grid_spacing, 400, grid_spacing):
            canvas_2d.create_line(0, y, 600, y, fill="lightgray", dash=(2, 4), tags="grid")
        for x in range(grid_spacing, 600, grid_spacing):
            canvas_2d.create_line(x, 0, x, 400, fill="lightgray", dash=(2, 4), tags="grid")
        canvas_2d.create_line(0, 200, 600, 200, fill="gray", width=2, tags="grid")
        canvas_2d.create_line(300, 0, 300, 400, fill="gray", width=2, tags="grid")
        canvas_2d.create_text(580, 220, text=axis_labels[0], font=("Arial", 12, "bold"), tags="grid")
        canvas_2d.create_text(280, 20, text=axis_labels[1], font=("Arial", 12, "bold"), tags="grid")
        canvas_2d.create_text(310, 220, text="(0,0)", font=("Arial", 8), tags="grid")
        for i in range(-5, 6):
            if i != 0:
                x_pos = 300 + i * grid_spacing
                canvas_2d.create_text(x_pos, 220, text=str(i), font=("Arial", 8), tags="grid")
                canvas_2d.create_line(x_pos, 198, x_pos, 202, fill="black", tags="grid")
                y_pos = 200 - i * grid_spacing
                canvas_2d.create_text(280, y_pos, text=str(i), font=("Arial", 8), tags="grid")
                canvas_2d.create_line(298, y_pos, 302, y_pos, fill="black", tags="grid")

    # 3D plot için figure oluştur
    fig = Figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection='3d')
    canvas_3d = FigureCanvasTkAgg(fig, master=preview_window_3d)
    canvas_3d.draw()
    canvas_3d.get_tk_widget().pack()

    # Yardımcı: Düzleme göre 2D projeksiyon koordinatı seçici
    def project2d(pt: tuple, plane: str):
        x, y, z = pt
        if plane == 'G18':  # XZ
            return x, z
        if plane == 'G19':  # YZ
            return y, z
        return x, y  # G17 XY

    def compute_bounds(paths, forced_plane: str | None):
        min_x = min_y = min_z = float('inf')
        max_x = max_y = max_z = float('-inf')
        for path in paths:
        # Sadece geçerli hareket yollarını işle
            if not (isinstance(path, dict) and 'start' in path and 'end' in path and 'type' in path):
                continue
            try:
                start_x, start_y, start_z = path['start']
                end_x, end_y, end_z = path['end']
            except Exception:
                continue
            if not all(isinstance(v, (int, float)) for v in [start_x, start_y, start_z, end_x, end_y, end_z]):
                continue
            min_x = min(min_x, start_x, end_x)
            max_x = max(max_x, start_x, end_x)
            min_y = min(min_y, start_y, end_y)
            max_y = max(max_y, start_y, end_y)
            min_z = min(min_z, start_z, end_z)
            max_z = max(max_z, start_z, end_z)
            if path['type'] == 'arc' and 'radius' in path and 'center_relative' in path:
                radius = path['radius']
                plane = forced_plane or path.get('plane', 'G17')
                crx, cry = path['center_relative']
                if plane == 'G18':
                    cx = start_x + crx
                    cy = start_z + cry
                elif plane == 'G19':
                    cx = start_y + crx
                    cy = start_z + cry
                else:
                    cx = start_x + crx
                    cy = start_y + cry
                if isinstance(radius, (int, float)):
                    min_x = min(min_x, cx - radius)
                    max_x = max(max_x, cx + radius)
                    min_y = min(min_y, cy - radius)
                    max_y = max(max_y, cy + radius)
        return min_x, max_x, min_y, max_y, min_z, max_z

    def compute_scale_and_offset(min_x, max_x, min_y, max_y):
        width = max_x - min_x
        height = max_y - min_y
        margin = max(width, height) * 0.1
        if any(v in (float('inf'), float('-inf')) for v in [min_x, max_x, min_y, max_y]) or width == 0 or height == 0:
            min_x = min_y = 0
            max_x = max_y = 100
            width = max_x - min_x
            height = max_y - min_y
        scale_x = (600 - 2*margin) / width if width > 0 else 1
        scale_y = (400 - 2*margin) / height if height > 0 else 1
        scale = min(scale_x, scale_y)
        x_offset = 300 - (min_x + max_x) * scale / 2
        y_offset = 200 - (min_y + max_y) * scale / 2
        return scale, x_offset, y_offset

    def draw_2d(paths, forced_plane: str | None):
        if forced_plane == 'G18':
            draw_grid(("X", "Z"))
        elif forced_plane == 'G19':
            draw_grid(("Y", "Z"))
        else:
            draw_grid(("X", "Y"))
        canvas_2d.delete("paths2d")
        min_x, max_x, min_y, max_y, _, _ = compute_bounds(paths, forced_plane)
        scale, x_offset, y_offset = compute_scale_and_offset(min_x, max_x, min_y, max_y)
        for path in paths:
            if not (isinstance(path, dict) and 'start' in path and 'end' in path and 'type' in path):
                continue
            try:
                start_x, start_y, start_z = path['start']
                end_x, end_y, end_z = path['end']
            except Exception:
                continue
            if not all(isinstance(v, (int, float)) for v in [start_x, start_y, start_z, end_x, end_y, end_z]):
                continue
            plane = forced_plane or path.get('plane', 'G17')
            sx2, sy2 = project2d((start_x, start_y, start_z), plane)
            ex2, ey2 = project2d((end_x, end_y, end_z), plane)
            if path['type'] == 'rapid':
                canvas_2d.create_line(
                    sx2 * scale + x_offset,
                    sy2 * scale + y_offset,
                    ex2 * scale + x_offset,
                    ey2 * scale + y_offset,
                    dash=(4, 4),
                    fill="blue",
                    tags="paths2d"
                )
            elif path['type'] == 'feed':
                canvas_2d.create_line(
                    sx2 * scale + x_offset,
                    sy2 * scale + y_offset,
                    ex2 * scale + x_offset,
                    ey2 * scale + y_offset,
                    fill="red",
                    tags="paths2d"
                )
            elif path['type'] == 'arc' and 'radius' in path and 'center_relative' in path and 'arc_type' in path:
                crx, cry = path['center_relative']
                if plane == 'G18':  # XZ
                    center_x, center_y = start_x + crx, start_z + cry
                    s_u, s_v = start_x, start_z
                    e_u, e_v = end_x, end_z
                elif plane == 'G19':  # YZ
                    center_x, center_y = start_y + crx, start_z + cry
                    s_u, s_v = start_y, start_z
                    e_u, e_v = end_y, end_z
                else:  # G17 XY
                    center_x, center_y = start_x + crx, start_y + cry
                    s_u, s_v = start_x, start_y
                    e_u, e_v = end_x, end_y
                radius = path['radius']
                if not isinstance(radius, (int, float)):
                    continue
                x1 = (center_x - radius) * scale + x_offset
                y1 = (center_y - radius) * scale + y_offset
                x2 = (center_x + radius) * scale + x_offset
                y2 = (center_y + radius) * scale + y_offset
                start_angle = math.degrees(math.atan2(s_v - center_y, s_u - center_x))
                end_angle = math.degrees(math.atan2(e_v - center_y, e_u - center_x))
                if path['arc_type'] == 'clockwise':
                    if end_angle > start_angle:
                        end_angle -= 360
                else:
                    if start_angle > end_angle:
                        start_angle -= 360
                extent = end_angle - start_angle if path['arc_type'] == 'counter_clockwise' else start_angle - end_angle
                canvas_2d.create_arc(
                    x1, y1, x2, y2,
                    start=start_angle,
                    extent=-extent if path['arc_type'] == 'clockwise' else extent,
                    style=tk.ARC,
                    outline="green",
                    width=2,
                    tags="paths2d"
                )

    # Başlangıçta Auto çizim
    draw_2d(paths, None)

    def on_plane_change(*_):
        sel = plane_var.get()
        forced = None
        if sel.startswith('G17') or sel == 'G17 (XY)':
            forced = 'G17'
        elif sel.startswith('G18') or sel == 'G18 (XZ)':
            forced = 'G18'
        elif sel.startswith('G19') or sel == 'G19 (YZ)':
            forced = 'G19'
        draw_2d(paths, forced)
    plane_var.trace_add('write', on_plane_change)

    # 3D çizim ve sınırlar
    # 3D eksen limitleri için kapsamı hesapla
    min_x, max_x, min_y, max_y, min_z, max_z = compute_bounds(paths, None)

    for path in paths:
        if not (isinstance(path, dict) and 'start' in path and 'end' in path and 'type' in path):
            continue
        try:
            start_x, start_y, start_z = path['start']
            end_x, end_y, end_z = path['end']
        except Exception:
            continue
        if not all(isinstance(v, (int, float)) for v in [start_x, start_y, start_z, end_x, end_y, end_z]):
            continue
        plane = path.get('plane', 'G17')
        if path['type'] in ('rapid', 'feed'):
            color = 'b' if path['type'] == 'rapid' else 'r'
            style = '--' if path['type'] == 'rapid' else '-'
            ax.plot([start_x, end_x], [start_y, end_y], [start_z, end_z], color=color, linestyle=style)
        elif path['type'] == 'arc' and 'radius' in path and 'center_relative' in path and 'arc_type' in path:
            crx, cry = path['center_relative']
            radius = path['radius']
            if not isinstance(radius, (int, float)):
                continue
            # Düzleme göre merkez ve başlangıç/bitiş açılarını hesapla
            if plane == 'G18':  # XZ
                center_x, center_y = start_x + crx, start_z + cry
                s_u, s_v = start_x, start_z
                e_u, e_v = end_x, end_z
            elif plane == 'G19':  # YZ
                center_x, center_y = start_y + crx, start_z + cry
                s_u, s_v = start_y, start_z
                e_u, e_v = end_y, end_z
            else:  # G17 XY
                center_x, center_y = start_x + crx, start_y + cry
                s_u, s_v = start_x, start_y
                e_u, e_v = end_x, end_y

            start_angle_rad = math.atan2(s_v - center_y, s_u - center_x)
            end_angle_rad = math.atan2(e_v - center_y, e_u - center_x)
            if path['arc_type'] == 'clockwise':
                if end_angle_rad > start_angle_rad:
                    end_angle_rad -= 2 * np.pi
            else:
                if start_angle_rad > end_angle_rad:
                    start_angle_rad -= 2 * np.pi
            theta = np.linspace(start_angle_rad, end_angle_rad, 100)
            if plane == 'G18':  # XZ
                xs = center_x + radius * np.cos(theta)
                zs = center_y + radius * np.sin(theta)
                ys = np.linspace(start_y, end_y, 100)
                ax.plot(xs, ys, zs, color='g')
            elif plane == 'G19':  # YZ
                ys = center_x + radius * np.cos(theta)
                zs = center_y + radius * np.sin(theta)
                xs = np.linspace(start_x, end_x, 100)
                ax.plot(xs, ys, zs, color='g')
            else:  # G17 XY
                xs = center_x + radius * np.cos(theta)
                ys = center_y + radius * np.sin(theta)
                zs = np.linspace(start_z, end_z, 100)
                ax.plot(xs, ys, zs, color='g')

    # 3D görünüm ayarları
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    
    # Görünümü eşit ölçekle ayarla
    if any(v in (float('inf'), float('-inf')) for v in [min_x, max_x, min_y, max_y, min_z, max_z]):
        # Geçerli veri yoksa varsayılan küçük bir küp göster
        min_x = min_y = min_z = -50
        max_x = max_y = max_z = 50
    max_range = max(max_x - min_x, max_y - min_y, max_z - min_z) or 1.0
    mid_x = (max_x + min_x) * 0.5
    mid_y = (max_y + min_y) * 0.5
    mid_z = (max_z + min_z) * 0.5
    ax.set_xlim(mid_x - max_range * 0.5, mid_x + max_range * 0.5)
    ax.set_ylim(mid_y - max_range * 0.5, mid_y + max_range * 0.5)
    ax.set_zlim(mid_z - max_range * 0.5, mid_z + max_range * 0.5)
    
    # Izgara ekle
    ax.grid(True)
    
    # 3D canvası güncelle
    canvas_3d.draw()

