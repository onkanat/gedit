import tkinter as tk
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from gcode_parser import parse_gcode
import math  # math modülünü ekle
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.lines import Line2D
import numpy as np

# Oturum boyunca 2D düzlem seçimini hatırla
_LAST_PLANE_SELECTION = "Auto"


def show_preview(editor, root):
    """
    G-code önizleme penceresini açar. 2D ve 3D görselleştirme sunar.
    :param editor: GCodeEditor instance
    :param root: Tkinter ana pencere
    """
    """G-code önizleme penceresini gösterir."""
    code = editor.get("1.0", tk.END)
    gcode_result = parse_gcode(code)
    paths = (
        gcode_result["paths"]
        if isinstance(gcode_result, dict) and "paths" in gcode_result
        else gcode_result
    )

    # Mevcut önizleme pencerelerini kapat
    for widget in root.winfo_children():
        if isinstance(widget, tk.Toplevel) and widget.title() in [
            "G-code Preview",
            "3D Preview",
        ]:
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
    global _LAST_PLANE_SELECTION
    plane_var = tk.StringVar(value=_LAST_PLANE_SELECTION)
    plane_options = ["Auto", "G17 (XY)", "G18 (XZ)", "G19 (YZ)"]
    tk.OptionMenu(ctrl_frame, plane_var, *plane_options).pack(side=tk.LEFT, padx=8)

    # Görünürlük anahtarları
    show_rapid = tk.BooleanVar(value=True)
    show_feed = tk.BooleanVar(value=True)
    show_arc = tk.BooleanVar(value=True)
    tk.Checkbutton(
        ctrl_frame,
        text="Rapid (G0)",
        variable=show_rapid,
        command=lambda: on_filter_change(),
    ).pack(side=tk.LEFT, padx=6)
    tk.Checkbutton(
        ctrl_frame,
        text="Feed (G1)",
        variable=show_feed,
        command=lambda: on_filter_change(),
    ).pack(side=tk.LEFT, padx=6)
    tk.Checkbutton(
        ctrl_frame,
        text="Arc (G2/G3)",
        variable=show_arc,
        command=lambda: on_filter_change(),
    ).pack(side=tk.LEFT, padx=6)

    canvas_2d = tk.Canvas(preview_window_2d, width=600, height=400, bg="white")
    canvas_2d.pack(padx=10, pady=10)

    def draw_grid(axis_labels=("X", "Y")):
        canvas_2d.delete("grid")
        grid_spacing = 50
        for y in range(grid_spacing, 400, grid_spacing):
            canvas_2d.create_line(
                0, y, 600, y, fill="lightgray", dash=(2, 4), tags="grid"
            )
        for x in range(grid_spacing, 600, grid_spacing):
            canvas_2d.create_line(
                x, 0, x, 400, fill="lightgray", dash=(2, 4), tags="grid"
            )
        canvas_2d.create_line(0, 200, 600, 200, fill="gray", width=2, tags="grid")
        canvas_2d.create_line(300, 0, 300, 400, fill="gray", width=2, tags="grid")
        canvas_2d.create_text(
            580, 220, text=axis_labels[0], font=("Arial", 12, "bold"), tags="grid"
        )
        canvas_2d.create_text(
            280, 20, text=axis_labels[1], font=("Arial", 12, "bold"), tags="grid"
        )
        canvas_2d.create_text(310, 220, text="(0,0)", font=("Arial", 8), tags="grid")
        for i in range(-5, 6):
            if i != 0:
                x_pos = 300 + i * grid_spacing
                canvas_2d.create_text(
                    x_pos, 220, text=str(i), font=("Arial", 8), tags="grid"
                )
                canvas_2d.create_line(x_pos, 198, x_pos, 202, fill="black", tags="grid")
                y_pos = 200 - i * grid_spacing
                canvas_2d.create_text(
                    280, y_pos, text=str(i), font=("Arial", 8), tags="grid"
                )
                canvas_2d.create_line(298, y_pos, 302, y_pos, fill="black", tags="grid")

    # 3D plot için figure oluştur
    fig = Figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection="3d")
    canvas_3d = FigureCanvasTkAgg(fig, master=preview_window_3d)
    canvas_3d.draw()
    canvas_3d.get_tk_widget().pack()

    # Yardımcı: Düzleme göre 2D projeksiyon koordinatı seçici
    def project2d(pt: tuple, plane: str):
        x, y, z = pt
        if plane == "G18":  # XZ
            return x, z
        if plane == "G19":  # YZ
            return y, z
        return x, y  # G17 XY

    def compute_bounds(paths, forced_plane: str | None):
        min_x = min_y = min_z = float("inf")
        max_x = max_y = max_z = float("-inf")

        # Düzleme göre projeksiyon koordinatları için sınırlar
        min_proj_x = min_proj_y = float("inf")
        max_proj_x = max_proj_y = float("-inf")

        for path in paths:
            # Sadece geçerli hareket yollarını işle
            if not (
                isinstance(path, dict)
                and "start" in path
                and ("end" in path or "end_tuple" in path)
                and "type" in path
            ):
                continue
            try:
                start_x, start_y, start_z = path["start"]
                # Enhanced parser uses different formats for end coordinates
                if "end_tuple" in path:
                    end_x, end_y, end_z = path["end_tuple"]
                elif isinstance(path["end"], tuple):
                    end_x, end_y, end_z = path["end"]
                elif isinstance(path["end"], dict):
                    end_x = path["end"].get("X", 0.0)
                    end_y = path["end"].get("Y", 0.0)
                    end_z = path["end"].get("Z", 0.0)
                else:
                    end_x, end_y, end_z = path["end"]
            except Exception:
                continue
            if not all(
                isinstance(v, (int, float))
                for v in [start_x, start_y, start_z, end_x, end_y, end_z]
            ):
                continue

            # 3D sınırları (her zaman hesapla)
            min_x = min(min_x, start_x, end_x)
            max_x = max(max_x, start_x, end_x)
            min_y = min(min_y, start_y, end_y)
            max_y = max(max_y, start_y, end_y)
            min_z = min(min_z, start_z, end_z)
            max_z = max(max_z, start_z, end_z)

            # 2D projeksiyon sınırları (forced_plane varsa)
            if forced_plane:
                plane = forced_plane or path.get("plane", "G17")
                sx2, sy2 = project2d((start_x, start_y, start_z), plane)
                ex2, ey2 = project2d((end_x, end_y, end_z), plane)
                min_proj_x = min(min_proj_x, sx2, ex2)
                max_proj_x = max(max_proj_x, sx2, ex2)
                min_proj_y = min(min_proj_y, sy2, ey2)
                max_proj_y = max(max_proj_y, sy2, ey2)

            if path["type"] == "arc" and "radius" in path and "center_relative" in path:
                radius = path["radius"]
                plane = forced_plane or path.get("plane", "G17")
                crx, cry = path["center_relative"]
                if plane == "G18":
                    cx = start_x + crx
                    cy = start_z + cry
                elif plane == "G19":
                    cx = start_y + crx
                    cy = start_z + cry
                else:
                    cx = start_x + crx
                    cy = start_y + cry
                if isinstance(radius, (int, float)):
                    # 3D sınırlar için
                    min_x = min(min_x, cx - radius)
                    max_x = max(max_x, cx + radius)
                    min_y = min(min_y, cy - radius)
                    max_y = max(max_y, cy + radius)

                    # 2D projeksiyon sınırları için (forced_plane varsa)
                    if forced_plane:
                        min_proj_x = min(min_proj_x, cx - radius)
                        max_proj_x = max(max_proj_x, cx + radius)
                        min_proj_y = min(min_proj_y, cy - radius)
                        max_proj_y = max(max_proj_y, cy + radius)

        # forced_plane varsa projeksiyon sınırlarını döndür, yoksa 3D sınırları
        if forced_plane and min_proj_x != float("inf"):
            return min_proj_x, max_proj_x, min_proj_y, max_proj_y, min_z, max_z
        else:
            return min_x, max_x, min_y, max_y, min_z, max_z

    def compute_scale_and_offset(min_x, max_x, min_y, max_y):
        width = max_x - min_x
        height = max_y - min_y
        margin = max(width, height) * 0.1
        if (
            any(
                v in (float("inf"), float("-inf")) for v in [min_x, max_x, min_y, max_y]
            )
            or width == 0
            or height == 0
        ):
            min_x = min_y = 0
            max_x = max_y = 100
            width = max_x - min_x
            height = max_y - min_y
        scale_x = (600 - 2 * margin) / width if width > 0 else 1
        scale_y = (400 - 2 * margin) / height if height > 0 else 1
        scale = min(scale_x, scale_y)
        x_offset = 300 - (min_x + max_x) * scale / 2
        y_offset = 200 - (min_y + max_y) * scale / 2
        return scale, x_offset, y_offset

    # Yumuşak geçiş için son ölçek/ofset değerleri
    last_scale = {"scale": 0.0, "x": 0.0, "y": 0.0, "initialized": False}

    def draw_legend2d():
        canvas_2d.delete("legend")
        x0, y0 = 10, 10
        dy = 18
        entries = []
        if show_rapid.get():
            entries.append(("Rapid", "blue", True))
        if show_feed.get():
            entries.append(("Feed", "red", False))
        if show_arc.get():
            entries.append(("Arc", "green", False))
        for i, (label, color, dashed) in enumerate(entries):
            y = y0 + i * dy
            if dashed:
                canvas_2d.create_line(
                    x0, y, x0 + 24, y, fill=color, dash=(4, 4), width=2, tags="legend"
                )
            else:
                canvas_2d.create_line(
                    x0, y, x0 + 24, y, fill=color, width=2, tags="legend"
                )
            canvas_2d.create_text(
                x0 + 30, y, text=label, anchor=tk.W, font=("Arial", 9), tags="legend"
            )

    def draw_2d(paths, forced_plane: str | None):
        if forced_plane == "G18":
            draw_grid(("X", "Z"))
        elif forced_plane == "G19":
            draw_grid(("Y", "Z"))
        else:
            draw_grid(("X", "Y"))
        canvas_2d.delete("paths2d")
        min_x, max_x, min_y, max_y, _, _ = compute_bounds(paths, forced_plane)
        scale, x_offset, y_offset = compute_scale_and_offset(min_x, max_x, min_y, max_y)
        # Yumuşatma: önceki ölçeğe/offsete doğru harmanla
        if last_scale["initialized"]:
            alpha = 0.6
            scale = alpha * scale + (1 - alpha) * last_scale["scale"]
            x_offset = alpha * x_offset + (1 - alpha) * last_scale["x"]
            y_offset = alpha * y_offset + (1 - alpha) * last_scale["y"]
        last_scale["scale"], last_scale["x"], last_scale["y"] = (
            float(scale),
            float(x_offset),
            float(y_offset),
        )
        last_scale["initialized"] = True
        for path in paths:
            # Diagnostikleri çizmeyin
            if isinstance(path, dict) and path.get("type") in (
                "unsupported",
                "unknown_param",
                "parse_error",
            ):
                continue
            if not (
                isinstance(path, dict)
                and "start" in path
                and ("end" in path or "end_tuple" in path)
                and "type" in path
            ):
                continue
            try:
                start_x, start_y, start_z = path["start"]
                # Enhanced parser uses different formats for end coordinates
                if "end_tuple" in path:
                    end_x, end_y, end_z = path["end_tuple"]
                elif isinstance(path["end"], tuple):
                    end_x, end_y, end_z = path["end"]
                elif isinstance(path["end"], dict):
                    end_x = path["end"].get("X", 0.0)
                    end_y = path["end"].get("Y", 0.0)
                    end_z = path["end"].get("Z", 0.0)
                else:
                    end_x, end_y, end_z = path["end"]
            except Exception:
                continue
            if not all(
                isinstance(v, (int, float))
                for v in [start_x, start_y, start_z, end_x, end_y, end_z]
            ):
                continue
            plane = forced_plane or path.get("plane", "G17")
            sx2, sy2 = project2d((start_x, start_y, start_z), plane)
            ex2, ey2 = project2d((end_x, end_y, end_z), plane)
            if path["type"] == "rapid":
                if not show_rapid.get():
                    continue
                canvas_2d.create_line(
                    sx2 * scale + x_offset,
                    sy2 * scale + y_offset,
                    ex2 * scale + x_offset,
                    ey2 * scale + y_offset,
                    dash=(4, 4),
                    fill="blue",
                    tags="paths2d",
                )
            elif path["type"] == "feed":
                if not show_feed.get():
                    continue
                canvas_2d.create_line(
                    sx2 * scale + x_offset,
                    sy2 * scale + y_offset,
                    ex2 * scale + x_offset,
                    ey2 * scale + y_offset,
                    fill="red",
                    tags="paths2d",
                )
            elif (
                path["type"] == "arc"
                and "radius" in path
                and "center_relative" in path
                and "arc_type" in path
            ):
                if not show_arc.get():
                    continue
                crx, cry = path["center_relative"]
                if plane == "G18":  # XZ
                    center_x, center_y = start_x + crx, start_z + cry
                    s_u, s_v = start_x, start_z
                    e_u, e_v = end_x, end_z
                elif plane == "G19":  # YZ
                    center_x, center_y = start_y + crx, start_z + cry
                    s_u, s_v = start_y, start_z
                    e_u, e_v = end_y, end_z
                else:  # G17 XY
                    center_x, center_y = start_x + crx, start_y + cry
                    s_u, s_v = start_x, start_y
                    e_u, e_v = end_x, end_y
                radius = path["radius"]
                if not isinstance(radius, (int, float)):
                    continue
                x1 = (center_x - radius) * scale + x_offset
                y1 = (center_y - radius) * scale + y_offset
                x2 = (center_x + radius) * scale + x_offset
                y2 = (center_y + radius) * scale + y_offset
                start_angle = math.degrees(math.atan2(s_v - center_y, s_u - center_x))
                end_angle = math.degrees(math.atan2(e_v - center_y, e_u - center_x))
                if path["arc_type"] == "clockwise":
                    if end_angle > start_angle:
                        end_angle -= 360
                else:
                    if start_angle > end_angle:
                        start_angle -= 360
                extent = (
                    end_angle - start_angle
                    if path["arc_type"] == "counter_clockwise"
                    else start_angle - end_angle
                )
                canvas_2d.create_arc(
                    x1,
                    y1,
                    x2,
                    y2,
                    start=start_angle,
                    extent=-extent if path["arc_type"] == "clockwise" else extent,
                    style=tk.ARC,
                    outline="green",
                    width=2,
                    tags="paths2d",
                )
        draw_legend2d()

    # 3D çizimi fonksiyona al (toggle ile yeniden çizmek için)
    def draw_3d(paths):
        ax.cla()
        # Görünür türler
        want_rapid = show_rapid.get()
        want_feed = show_feed.get()
        want_arc = show_arc.get()
        # Sınırları hesapla
        min_x, max_x, min_y, max_y, min_z, max_z = compute_bounds(paths, None)
        for path in paths:
            # Diagnostikleri çizmeyin
            if isinstance(path, dict) and path.get("type") in (
                "unsupported",
                "unknown_param",
                "parse_error",
            ):
                continue
            if not (
                isinstance(path, dict)
                and "start" in path
                and ("end" in path or "end_tuple" in path)
                and "type" in path
            ):
                continue
            try:
                start_x, start_y, start_z = path["start"]
                # Enhanced parser uses different formats for end coordinates
                if "end_tuple" in path:
                    end_x, end_y, end_z = path["end_tuple"]
                elif isinstance(path["end"], tuple):
                    end_x, end_y, end_z = path["end"]
                elif isinstance(path["end"], dict):
                    end_x = path["end"].get("X", 0.0)
                    end_y = path["end"].get("Y", 0.0)
                    end_z = path["end"].get("Z", 0.0)
                else:
                    end_x, end_y, end_z = path["end"]
            except Exception:
                continue
            if not all(
                isinstance(v, (int, float))
                for v in [start_x, start_y, start_z, end_x, end_y, end_z]
            ):
                continue
            plane = path.get("plane", "G17")
            if path["type"] == "rapid" and want_rapid:
                ax.plot(
                    [start_x, end_x],
                    [start_y, end_y],
                    [start_z, end_z],
                    color="b",
                    linestyle="--",
                )
            elif path["type"] == "feed" and want_feed:
                ax.plot(
                    [start_x, end_x],
                    [start_y, end_y],
                    [start_z, end_z],
                    color="r",
                    linestyle="-",
                )
            elif (
                path["type"] == "arc"
                and want_arc
                and "radius" in path
                and "center_relative" in path
                and "arc_type" in path
            ):
                crx, cry = path["center_relative"]
                radius = path["radius"]
                if not isinstance(radius, (int, float)):
                    continue
                if plane == "G18":  # XZ
                    center_x, center_y = start_x + crx, start_z + cry
                    s_u, s_v = start_x, start_z
                    e_u, e_v = end_x, end_z
                elif plane == "G19":  # YZ
                    center_x, center_y = start_y + crx, start_z + cry
                    s_u, s_v = start_y, start_z
                    e_u, e_v = end_y, end_z
                else:  # G17 XY
                    center_x, center_y = start_x + crx, start_y + cry
                    s_u, s_v = start_x, start_y
                    e_u, e_v = end_x, end_y
                start_angle_rad = math.atan2(s_v - center_y, s_u - center_x)
                end_angle_rad = math.atan2(e_v - center_y, e_u - center_x)
                if path["arc_type"] == "clockwise":
                    if end_angle_rad > start_angle_rad:
                        end_angle_rad -= 2 * np.pi
                else:
                    if start_angle_rad > end_angle_rad:
                        start_angle_rad -= 2 * np.pi
                theta = np.linspace(start_angle_rad, end_angle_rad, 100)
                if plane == "G18":  # XZ
                    xs = center_x + radius * np.cos(theta)
                    zs = center_y + radius * np.sin(theta)
                    ys = np.linspace(start_y, end_y, 100)
                    ax.plot(xs, ys, zs, color="g")
                elif plane == "G19":  # YZ
                    ys = center_x + radius * np.cos(theta)
                    zs = center_y + radius * np.sin(theta)
                    xs = np.linspace(start_x, end_x, 100)
                    ax.plot(xs, ys, zs, color="g")
                else:  # G17 XY
                    xs = center_x + radius * np.cos(theta)
                    ys = center_y + radius * np.sin(theta)
                    zs = np.linspace(start_z, end_z, 100)
                    ax.plot(xs, ys, zs, color="g")
        # 3D görünüm ayarları ve sınırlar
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_zlabel("Z")
        if any(
            v in (float("inf"), float("-inf"))
            for v in [min_x, max_x, min_y, max_y, min_z, max_z]
        ):
            min_x = min_y = min_z = -50
            max_x = max_y = max_z = 50
        max_range = max(max_x - min_x, max_y - min_y, max_z - min_z) or 1.0
        mid_x = (max_x + min_x) * 0.5
        mid_y = (max_y + min_y) * 0.5
        mid_z = (max_z + min_z) * 0.5
        ax.set_xlim(mid_x - max_range * 0.5, mid_x + max_range * 0.5)
        ax.set_ylim(mid_y - max_range * 0.5, mid_y + max_range * 0.5)
        ax.set_zlim(mid_z - max_range * 0.5, mid_z + max_range * 0.5)
        ax.grid(True)
        # Legend: sadece açık olanları göster
        handles = []
        if show_rapid.get():
            handles.append(
                Line2D([0], [0], color="b", linestyle="--", label="Rapid (G0)")
            )
        if show_feed.get():
            handles.append(
                Line2D([0], [0], color="r", linestyle="-", label="Feed (G1)")
            )
        if show_arc.get():
            handles.append(
                Line2D([0], [0], color="g", linestyle="-", label="Arc (G2/G3)")
            )
        if handles:
            ax.legend(handles=handles, loc="upper right")
        canvas_3d.draw()

    # Başlangıçta çizimler
    draw_2d(paths, None)
    draw_3d(paths)

    def on_plane_change(*_):
        global _LAST_PLANE_SELECTION
        sel = plane_var.get()
        forced = None
        if sel.startswith("G17") or sel == "G17 (XY)":
            forced = "G17"
        elif sel.startswith("G18") or sel == "G18 (XZ)":
            forced = "G18"
        elif sel.startswith("G19") or sel == "G19 (YZ)":
            forced = "G19"
        _LAST_PLANE_SELECTION = sel
        draw_2d(paths, forced)
        draw_3d(paths)

    plane_var.trace_add("write", on_plane_change)

    def on_filter_change():
        sel = plane_var.get()
        forced = None
        if sel.startswith("G17") or sel == "G17 (XY)":
            forced = "G17"
        elif sel.startswith("G18") or sel == "G18 (XZ)":
            forced = "G18"
        elif sel.startswith("G19") or sel == "G19 (YZ)":
            forced = "G19"
        draw_2d(paths, forced)
        draw_3d(paths)
