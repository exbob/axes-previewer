#!/usr/bin/env python3
"""
Interactive 3D Cartesian preview: edit cube label, face dot, and axis mapping in a GUI,
export PNG/SVG. Reuses cartesian_3d.py in this directory without modifying that module.

Adapts Tk scaling and Matplotlib figure DPI from the display PPI so the UI stays usable
on 4K / high-DPI monitors (Windows per-monitor DPI awareness is enabled before Tk starts).
"""
from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import tkinter as tk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# Ensure cartesian_3d is importable when run from repo root or from scripts/
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import cartesian_3d as c3d  # noqa: E402

# Same keys as cartesian_3d axis direction vocabulary (for combobox values).
_DIRECTION_CHOICES = ("back", "down", "front", "left", "right", "up")
_FACE_CHOICES = ("up", "down", "front", "back", "left", "right")
_CORNER_CHOICES = ("left_top", "left_bottom", "right_top", "right_bottom")
_TEXT_AXIS_CHOICES = ("x", "-x", "y", "-y", "z", "-z")

# Gap between right-aligned labels and the following Entry/Combobox (px, left, right).
_LABEL_PAD_AFTER = (0, 10)

# HiDPI / 4K: Tk and Matplotlib default to ~96 PPI logic, which looks tiny on 4K.
_REFERENCE_PPI = 96.0
_FIG_DPI_MIN = 96
_FIG_DPI_MAX = 192

# Interactive figure size (inches); primary driver of default window size.
_DEFAULT_FIGSIZE_INCHES = (12.0, 12.0)


def _pixels_per_inch(root: tk.Tk) -> float:
    """Physical pixels per inch for the root window's screen (fallback: 96)."""
    try:
        return float(root.winfo_fpixels("1i"))
    except tk.TclError:
        return _REFERENCE_PPI


def _apply_tk_scaling_for_display(root: tk.Tk) -> float:
    """
    Match Tk point scaling to display DPI so ttk fonts and layout scale on 4K.

    Returns measured PPI for reuse (e.g. Matplotlib figure DPI).
    """
    root.update_idletasks()
    ppi = _pixels_per_inch(root)
    try:
        root.tk.call("tk", "scaling", "-displayof", ".", ppi / 72.0)
    except tk.TclError:
        pass
    return ppi


def _figure_dpi_for_display(ppi: float) -> int:
    """Figure DPI scales with PPI; capped so the default window stays reasonable."""
    scaled = int(round(100.0 * (ppi / _REFERENCE_PPI)))
    return max(_FIG_DPI_MIN, min(_FIG_DPI_MAX, scaled))


def _plot_column_minsize(ppi: float) -> int:
    """Minimum width (px) for the plot column; grows slightly on high-DPI screens."""
    base = 360
    return max(base, min(860, int(float(base) * (ppi / _REFERENCE_PPI))))


def _build_center_config_from_ui(state: dict) -> c3d.center_object_config_t:
    try:
        radius = float(state["face_dot_radius"])
        edge_off = float(state["face_dot_edge_offset"])
    except (TypeError, ValueError) as exc:
        raise ValueError("Dot radius and edge offset must be numbers") from exc
    return replace(
        c3d.DEFAULT_CENTER_OBJECT,
        face_text=state["face_text"].strip() or " ",
        face_name=state["face_name"],
        face_text_axis=state["face_text_axis"],
        face_dot_enabled=bool(state["face_dot_enabled"]),
        face_dot_name=state["face_dot_name"],
        face_dot_corner=state["face_dot_corner"],
        face_dot_radius=radius,
        face_dot_edge_offset=edge_off,
        axis_labels=(
            state["axis_label_x"].strip() or "X",
            state["axis_label_y"].strip() or "Y",
            state["axis_label_z"].strip() or "Z",
        ),
        axis_directions=(state["axis_dir_x"], state["axis_dir_y"], state["axis_dir_z"]),
    )


def _build_corner_config_from_ui(state: dict) -> c3d.corner_axes_config_t:
    return replace(
        c3d.DEFAULT_CORNER_AXES,
        labels=(
            state["corner_e"].strip() or "E",
            state["corner_n"].strip() or "N",
            state["corner_u"].strip() or "U",
        ),
    )


class Cartesian3DEditorApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("3D Cartesian preview — editor")
        self._ppi = _apply_tk_scaling_for_display(self.root)
        self.limit = 10.0
        self.view = c3d.DEFAULT_VIEW

        fig_dpi = _figure_dpi_for_display(self._ppi)
        self.fig = Figure(figsize=_DEFAULT_FIGSIZE_INCHES, dpi=fig_dpi)
        self.ax = self.fig.add_subplot(111, projection="3d")
        self.canvas = None  # created in _build_layout with correct parent

        self._vars = self._make_vars()
        self._build_layout()
        self._center_root_window()
        self.root.update_idletasks()
        self._redraw()

    def _center_root_window(self) -> None:
        """Place the root window in the center of the primary screen on startup."""
        root = self.root
        root.update_idletasks()
        req_w = root.winfo_reqwidth()
        req_h = root.winfo_reqheight()
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        x = max(0, (sw - req_w) // 2)
        y = max(0, (sh - req_h) // 2)
        root.geometry(f"+{x}+{y}")

    def _make_vars(self) -> dict:
        co = c3d.DEFAULT_CENTER_OBJECT
        cor = c3d.DEFAULT_CORNER_AXES
        return {
            "face_text": tk.StringVar(value=co.face_text),
            "face_name": tk.StringVar(value=co.face_name),
            "face_text_axis": tk.StringVar(value=co.face_text_axis),
            "face_dot_enabled": tk.BooleanVar(value=co.face_dot_enabled),
            "face_dot_name": tk.StringVar(value=co.face_dot_name),
            "face_dot_corner": tk.StringVar(value=co.face_dot_corner),
            "face_dot_radius": tk.StringVar(value=str(co.face_dot_radius)),
            "face_dot_edge_offset": tk.StringVar(value=str(co.face_dot_edge_offset)),
            "axis_label_x": tk.StringVar(value=co.axis_labels[0]),
            "axis_label_y": tk.StringVar(value=co.axis_labels[1]),
            "axis_label_z": tk.StringVar(value=co.axis_labels[2]),
            "axis_dir_x": tk.StringVar(value=co.axis_directions[0]),
            "axis_dir_y": tk.StringVar(value=co.axis_directions[1]),
            "axis_dir_z": tk.StringVar(value=co.axis_directions[2]),
            "corner_e": tk.StringVar(value=cor.labels[0]),
            "corner_n": tk.StringVar(value=cor.labels[1]),
            "corner_u": tk.StringVar(value=cor.labels[2]),
        }

    def _build_layout(self) -> None:
        # Use grid instead of Panedwindow: some themes collapse the first pane to
        # zero width, which hides the 3D plot on the left.
        main = ttk.Frame(self.root)
        main.pack(fill=tk.BOTH, expand=True)
        main.columnconfigure(0, weight=1, minsize=_plot_column_minsize(self._ppi))
        main.columnconfigure(1, weight=0)
        main.rowconfigure(0, weight=1)

        plot = ttk.Frame(main)
        ctrl = ttk.Frame(main, padding=8)
        plot.grid(row=0, column=0, sticky="nsew")
        ctrl.grid(row=0, column=1, sticky="nsew")

        self.canvas = FigureCanvasTkAgg(self.fig, master=plot)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill=tk.BOTH, expand=True)

        row = 0
        lf_cube = ttk.LabelFrame(ctrl, text="Cube face text", padding=6)
        lf_cube.grid(row=row, column=0, sticky="ew")
        row += 1
        ttk.Label(lf_cube, text="Text").grid(row=0, column=0, sticky="e", padx=_LABEL_PAD_AFTER)
        ttk.Entry(lf_cube, textvariable=self._vars["face_text"], width=18).grid(
            row=0, column=1, sticky="ew"
        )
        ttk.Label(lf_cube, text="Face").grid(
            row=1, column=0, sticky="e", padx=_LABEL_PAD_AFTER, pady=(4, 0)
        )
        ttk.Combobox(
            lf_cube,
            textvariable=self._vars["face_name"],
            values=_FACE_CHOICES,
            state="readonly",
            width=16,
        ).grid(row=1, column=1, sticky="ew", pady=(4, 0))
        ttk.Label(lf_cube, text="In-face axis").grid(
            row=2, column=0, sticky="e", padx=_LABEL_PAD_AFTER, pady=(4, 0)
        )
        ttk.Combobox(
            lf_cube,
            textvariable=self._vars["face_text_axis"],
            values=_TEXT_AXIS_CHOICES,
            state="readonly",
            width=16,
        ).grid(row=2, column=1, sticky="ew", pady=(4, 0))
        lf_cube.columnconfigure(1, weight=1)

        lf_dot = ttk.LabelFrame(ctrl, text="Face dot", padding=6)
        lf_dot.grid(row=row, column=0, sticky="ew", pady=(8, 0))
        row += 1
        ttk.Checkbutton(
            lf_dot, text="Show dot", variable=self._vars["face_dot_enabled"]
        ).grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(lf_dot, text="Face").grid(
            row=1, column=0, sticky="e", padx=_LABEL_PAD_AFTER, pady=(4, 0)
        )
        ttk.Combobox(
            lf_dot,
            textvariable=self._vars["face_dot_name"],
            values=_FACE_CHOICES,
            state="readonly",
            width=16,
        ).grid(row=1, column=1, sticky="ew", pady=(4, 0))
        ttk.Label(lf_dot, text="Corner").grid(
            row=2, column=0, sticky="e", padx=_LABEL_PAD_AFTER, pady=(4, 0)
        )
        ttk.Combobox(
            lf_dot,
            textvariable=self._vars["face_dot_corner"],
            values=_CORNER_CHOICES,
            state="readonly",
            width=16,
        ).grid(row=2, column=1, sticky="ew", pady=(4, 0))
        ttk.Label(lf_dot, text="Radius").grid(
            row=3, column=0, sticky="e", padx=_LABEL_PAD_AFTER, pady=(4, 0)
        )
        ttk.Entry(lf_dot, textvariable=self._vars["face_dot_radius"], width=10).grid(
            row=3, column=1, sticky="w", pady=(4, 0)
        )
        ttk.Label(lf_dot, text="Edge offset").grid(
            row=4, column=0, sticky="e", padx=_LABEL_PAD_AFTER, pady=(4, 0)
        )
        ttk.Entry(lf_dot, textvariable=self._vars["face_dot_edge_offset"], width=10).grid(
            row=4, column=1, sticky="w", pady=(4, 0)
        )
        lf_dot.columnconfigure(1, weight=1)

        lf_axes = ttk.LabelFrame(ctrl, text="Body axes (center)", padding=6)
        lf_axes.grid(row=row, column=0, sticky="ew", pady=(8, 0))
        row += 1
        for i, (lbl, key_l, key_d) in enumerate(
            (
                ("X", "axis_label_x", "axis_dir_x"),
                ("Y", "axis_label_y", "axis_dir_y"),
                ("Z", "axis_label_z", "axis_dir_z"),
            )
        ):
            r = i * 2
            ttk.Label(lf_axes, text=f"{lbl} label").grid(
                row=r, column=0, sticky="e", padx=_LABEL_PAD_AFTER
            )
            ttk.Entry(lf_axes, textvariable=self._vars[key_l], width=8).grid(
                row=r, column=1, sticky="w"
            )
            ttk.Label(lf_axes, text="Direction").grid(
                row=r + 1, column=0, sticky="e", padx=_LABEL_PAD_AFTER, pady=(2, 0)
            )
            ttk.Combobox(
                lf_axes,
                textvariable=self._vars[key_d],
                values=_DIRECTION_CHOICES,
                state="readonly",
                width=14,
            ).grid(row=r + 1, column=1, sticky="w", pady=(2, 0))
        lf_axes.columnconfigure(1, weight=1)

        lf_corner = ttk.LabelFrame(ctrl, text="Corner reference labels (ENU)", padding=6)
        lf_corner.grid(row=row, column=0, sticky="ew", pady=(8, 0))
        row += 1
        for i, (lab, key) in enumerate(
            (("E", "corner_e"), ("N", "corner_n"), ("U", "corner_u"))
        ):
            ttk.Label(lf_corner, text=lab).grid(
                row=i, column=0, sticky="e", padx=_LABEL_PAD_AFTER, pady=(2, 0)
            )
            ttk.Entry(lf_corner, textvariable=self._vars[key], width=12).grid(
                row=i, column=1, sticky="ew", pady=(2, 0)
            )
        lf_corner.columnconfigure(1, weight=1)

        btn_row = ttk.Frame(ctrl, padding=(0, 10, 0, 0))
        btn_row.grid(row=row, column=0, sticky="ew")
        row += 1
        ttk.Button(btn_row, text="Apply / redraw", command=self._on_apply).pack(
            fill=tk.X, pady=2
        )
        ttk.Button(btn_row, text="Export PNG...", command=self._export_png).pack(
            fill=tk.X, pady=2
        )
        ttk.Button(btn_row, text="Export SVG...", command=self._export_svg).pack(
            fill=tk.X, pady=2
        )

        ctrl.columnconfigure(0, weight=1)

    def _collect_state(self) -> dict:
        return {k: v.get() for k, v in self._vars.items()}

    def _redraw(self) -> None:
        state = self._collect_state()
        try:
            center = _build_center_config_from_ui(state)
            corner = _build_corner_config_from_ui(state)
        except ValueError as exc:
            messagebox.showerror("Invalid input", str(exc))
            return

        try:
            self.ax.clear()
            c3d.setup_base_cartesian_scene(self.ax, self.limit, self.view)
            c3d.draw_background_axes(self.ax, self.limit)
            c3d.add_corner_reference_axes(self.ax, self.limit, corner)
            c3d.add_center_cube_with_axes(self.ax, center)
            self.canvas.draw()
        except ValueError as exc:
            messagebox.showerror("Draw failed", str(exc))

    def _on_apply(self) -> None:
        self._redraw()

    def _export_png(self) -> None:
        path = filedialog.asksaveasfilename(
            parent=self.root,
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("All", "*.*")],
        )
        if not path:
            return
        state = self._collect_state()
        try:
            center = _build_center_config_from_ui(state)
            corner = _build_corner_config_from_ui(state)
        except ValueError as exc:
            messagebox.showerror("Invalid input", str(exc))
            return
        fig = Figure(figsize=(8, 8), dpi=300)
        ax = fig.add_subplot(111, projection="3d")
        try:
            c3d.setup_base_cartesian_scene(ax, self.limit, self.view)
            c3d.draw_background_axes(ax, self.limit)
            c3d.add_corner_reference_axes(ax, self.limit, corner)
            c3d.add_center_cube_with_axes(ax, center)
            fig.savefig(Path(path), format="png", dpi=300, bbox_inches="tight")
        except ValueError as exc:
            messagebox.showerror("Export failed", str(exc))
            return
        messagebox.showinfo("Done", f"Saved: {path}")

    def _export_svg(self) -> None:
        path = filedialog.asksaveasfilename(
            parent=self.root,
            defaultextension=".svg",
            filetypes=[("SVG", "*.svg"), ("All", "*.*")],
        )
        if not path:
            return
        state = self._collect_state()
        try:
            center = _build_center_config_from_ui(state)
            corner = _build_corner_config_from_ui(state)
        except ValueError as exc:
            messagebox.showerror("Invalid input", str(exc))
            return
        fig = Figure(figsize=(8, 8))
        ax = fig.add_subplot(111, projection="3d")
        try:
            c3d.setup_base_cartesian_scene(ax, self.limit, self.view)
            c3d.draw_background_axes(ax, self.limit)
            c3d.add_corner_reference_axes(ax, self.limit, corner)
            c3d.add_center_cube_with_axes(ax, center)
            fig.savefig(Path(path), format="svg", bbox_inches="tight")
        except ValueError as exc:
            messagebox.showerror("Export failed", str(exc))
            return
        messagebox.showinfo("Done", f"Saved: {path}")

    def run(self) -> None:
        self.root.mainloop()


def _windows_set_per_monitor_dpi_awareness() -> None:
    """Improve PPI detection on 4K Windows; must run before tk.Tk()."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
    except ImportError:
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except (AttributeError, OSError):
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            pass


def main() -> None:
    _windows_set_per_monitor_dpi_awareness()
    Cartesian3DEditorApp().run()


if __name__ == "__main__":
    main()
