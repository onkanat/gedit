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

    # 2D canvas oluştur ve grid çiz
    canvas_2d = tk.Canvas(preview_window_2d, width=600, height=400, bg="white")
    canvas_2d.pack(padx=10, pady=10)

    # Grid çizgilerini çiz
    grid_spacing = 50  # Grid aralığı (piksel)
    
    # Yatay grid çizgileri
    for y in range(grid_spacing, 400, grid_spacing):
        canvas_2d.create_line(0, y, 600, y, fill="lightgray", dash=(2, 4))
    
    # Dikey grid çizgileri
    for x in range(grid_spacing, 600, grid_spacing):
        canvas_2d.create_line(x, 0, x, 400, fill="lightgray", dash=(2, 4))

    # Ana eksen çizgileri (kalın ve sürekli)
    canvas_2d.create_line(0, 200, 600, 200, fill="gray", width=2)  # X ekseni
    canvas_2d.create_line(300, 0, 300, 400, fill="gray", width=2)  # Y ekseni

    # Eksen etiketleri
    canvas_2d.create_text(580, 220, text="X", font=("Arial", 12, "bold"))
    canvas_2d.create_text(280, 20, text="Y", font=("Arial", 12, "bold"))

    # Merkez noktası etiketi (0,0)
    canvas_2d.create_text(310, 220, text="(0,0)", font=("Arial", 8))

    # Ölçek değerleri
    for i in range(-5, 6):
        if i != 0:
            # X ekseni ölçek değerleri
            x_pos = 300 + i * grid_spacing
            canvas_2d.create_text(x_pos, 220, text=str(i), font=("Arial", 8))
            canvas_2d.create_line(x_pos, 198, x_pos, 202, fill="black")  # Ölçek çizgisi
            
            # Y ekseni ölçek değerleri
            y_pos = 200 - i * grid_spacing
            canvas_2d.create_text(280, y_pos, text=str(i), font=("Arial", 8))
            canvas_2d.create_line(298, y_pos, 302, y_pos, fill="black")  # Ölçek çizgisi

    # 3D plot için figure oluştur
    fig = Figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection='3d')
    canvas_3d = FigureCanvasTkAgg(fig, master=preview_window_3d)
    canvas_3d.draw()
    canvas_3d.get_tk_widget().pack()

    # Sınırları hesapla
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
            center_x = start_x + path['center_relative'][0]
            center_y = start_y + path['center_relative'][1]
            if isinstance(radius, (int, float)):
                min_x = min(min_x, center_x - radius)
                max_x = max(max_x, center_x + radius)
                min_y = min(min_y, center_y - radius)
                max_y = max(max_y, center_y + radius)

    width = max_x - min_x
    height = max_y - min_y
    margin = max(width, height) * 0.1

    # Ölçeklendirme faktörünü hesapla
    scale_x = (600 - 2*margin) / width if width > 0 else 1
    scale_y = (400 - 2*margin) / height if height > 0 else 1
    scale = min(scale_x, scale_y)

    # Merkezi offset hesapla
    x_offset = 300 - (min_x + max_x) * scale / 2
    y_offset = 200 - (min_y + max_y) * scale / 2

    # Yolları çiz (2D ve 3D)
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
        # 2D çizim
        if path['type'] == 'rapid':
            canvas_2d.create_line(
                start_x * scale + x_offset,
                start_y * scale + y_offset,
                end_x * scale + x_offset,
                end_y * scale + y_offset,
                dash=(4, 4),
                fill="blue"
            )
            ax.plot([start_x, end_x], [start_y, end_y], [start_z, end_z], color='b', linestyle='--')
        elif path['type'] == 'feed':
            canvas_2d.create_line(
                start_x * scale + x_offset,
                start_y * scale + y_offset,
                end_x * scale + x_offset,
                end_y * scale + y_offset,
                fill="red"
            )
            ax.plot([start_x, end_x], [start_y, end_y], [start_z, end_z], color='r', linestyle='-')
        elif path['type'] == 'arc' and 'radius' in path and 'center_relative' in path and 'arc_type' in path:
            center_x = start_x + path['center_relative'][0]
            center_y = start_y + path['center_relative'][1]
            radius = path['radius']
            if not isinstance(radius, (int, float)):
                continue
            x1 = (center_x - radius) * scale + x_offset
            y1 = (center_y - radius) * scale + y_offset
            x2 = (center_x + radius) * scale + x_offset
            y2 = (center_y + radius) * scale + y_offset
            start_angle = math.degrees(math.atan2(start_y - center_y, start_x - center_x))
            end_angle = math.degrees(math.atan2(end_y - center_y, end_x - center_x))
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
                width=2
            )
            # 3D arc çizimi
            start_angle_rad = math.atan2(start_y - center_y, start_x - center_x)
            end_angle_rad = math.atan2(end_y - center_y, end_x - center_x)
            if path['arc_type'] == 'clockwise':
                if end_angle_rad > start_angle_rad:
                    end_angle_rad -= 2 * np.pi
            else:
                if start_angle_rad > end_angle_rad:
                    start_angle_rad -= 2 * np.pi
            theta = np.linspace(start_angle_rad, end_angle_rad, 100)
            x = center_x + radius * np.cos(theta)
            y = center_y + radius * np.sin(theta)
            z = np.linspace(start_z, end_z, 100)
            ax.plot(x, y, z, color='g')

    # 3D görünüm ayarları
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    
    # Görünümü eşit ölçekle ayarla
    max_range = max(max_x - min_x, max_y - min_y, max_z - min_z)
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

