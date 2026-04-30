#!/usr/bin/env python3
import argparse
from dataclasses import dataclass

import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


@dataclass(frozen=True)
class view_config_t:
    elev: float = 20
    azim: float = -30
    proj_type: str = "persp"
    focal_length: float = 0.65
    grid_alpha: float = 0.35
    box_aspect: tuple = (1, 1, 1)

@dataclass(frozen=True)
class corner_axes_config_t:
    length: float = 2
    padding: float = 1.2
    color: str = "k"
    linewidth: float = 1.6
    arrow_length_ratio: float = 0.2
    labels: tuple = ("E", "N", "U")
    label_offset: float = 0.15

@dataclass(frozen=True)
class center_object_config_t:
    cube_size: float = 4
    cube_color: str = "green"
    cube_alpha: float = 0.28
    axis_length: float = 7
    axis_colors: tuple = ("r", "y", "b")
    axis_labels: tuple = ("X", "Y", "Z")
    axis_label_size: float = 16
    axis_label_weight: str = "bold"
    axis_label_offset: float = 0.2


DEFAULT_VIEW = view_config_t()
DEFAULT_CORNER_AXES = corner_axes_config_t()
DEFAULT_CENTER_OBJECT = center_object_config_t()


def setup_base_cartesian_scene(ax, limit, view):
    ax.set_xlim(-limit, limit)
    ax.set_ylim(-limit, limit)
    ax.set_zlim(-limit, limit)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.set_title("3D Cartesian Coordinate System")
    ax.grid(True, alpha=view.grid_alpha)
    ax.set_box_aspect(view.box_aspect)
    ax.xaxis.set_major_locator(MultipleLocator(2))
    ax.yaxis.set_major_locator(MultipleLocator(2))
    ax.zaxis.set_major_locator(MultipleLocator(2))
    ax.view_init(elev=view.elev, azim=view.azim)
    if view.proj_type == "persp":
        ax.set_proj_type("persp", focal_length=view.focal_length)
    else:
        ax.set_proj_type("ortho")


def draw_background_axes(ax, limit):
    ax.plot([-limit, limit], [0, 0], [0, 0], color="0.35", linestyle="--", linewidth=1.4)
    ax.plot([0, 0], [-limit, limit], [0, 0], color="0.35", linestyle="--", linewidth=1.4)
    ax.plot([0, 0], [0, 0], [-limit, limit], color="0.35", linestyle="--", linewidth=1.4)

    label_offset = limit * 1.05
    ax.text(label_offset, 0, 0, "Right", color="0.35")
    ax.text(-label_offset, 0, 0, "Left", color="0.35")
    ax.text(0, label_offset, 0, "Front", color="0.35")
    ax.text(0, -label_offset, 0, "Back", color="0.35")
    ax.text(0, 0, label_offset, "Up", color="0.35")
    ax.text(0, 0, -label_offset, "Down", color="0.35")


def add_corner_reference_axes(ax, limit, config):
    corner_origin = (
        -limit + config.padding,
        -limit + config.padding,
        -limit + config.padding,
    )
    ax.quiver(
        *corner_origin,
        config.length,
        0,
        0,
        color=config.color,
        linewidth=config.linewidth,
        arrow_length_ratio=config.arrow_length_ratio,
    )
    ax.quiver(
        *corner_origin,
        0,
        config.length,
        0,
        color=config.color,
        linewidth=config.linewidth,
        arrow_length_ratio=config.arrow_length_ratio,
    )
    ax.quiver(
        *corner_origin,
        0,
        0,
        config.length,
        color=config.color,
        linewidth=config.linewidth,
        arrow_length_ratio=config.arrow_length_ratio,
    )
    ax.text(
        corner_origin[0] + config.length + config.label_offset,
        corner_origin[1],
        corner_origin[2],
        config.labels[0],
        color=config.color,
    )
    ax.text(
        corner_origin[0],
        corner_origin[1] + config.length + config.label_offset,
        corner_origin[2],
        config.labels[1],
        color=config.color,
    )
    ax.text(
        corner_origin[0],
        corner_origin[1],
        corner_origin[2] + config.length + config.label_offset,
        config.labels[2],
        color=config.color,
    )


def add_center_cube_with_axes(ax, config):
    half = config.cube_size / 2
    vertices = [
        (-half, -half, -half),
        (half, -half, -half),
        (half, half, -half),
        (-half, half, -half),
        (-half, -half, half),
        (half, -half, half),
        (half, half, half),
        (-half, half, half),
    ]
    faces = [
        [vertices[0], vertices[1], vertices[2], vertices[3]],
        [vertices[4], vertices[5], vertices[6], vertices[7]],
        [vertices[0], vertices[1], vertices[5], vertices[4]],
        [vertices[2], vertices[3], vertices[7], vertices[6]],
        [vertices[1], vertices[2], vertices[6], vertices[5]],
        [vertices[4], vertices[7], vertices[3], vertices[0]],
    ]
    cube = Poly3DCollection(
        faces,
        facecolors=config.cube_color,
        edgecolors=config.cube_color,
        linewidths=1,
        alpha=config.cube_alpha,
    )
    ax.add_collection3d(cube)

    ax.quiver(0, 0, 0, config.axis_length, 0, 0, color=config.axis_colors[0], linewidth=2, arrow_length_ratio=0.08)
    ax.quiver(0, 0, 0, 0, config.axis_length, 0, color=config.axis_colors[1], linewidth=2, arrow_length_ratio=0.08)
    ax.quiver(0, 0, 0, 0, 0, config.axis_length, color=config.axis_colors[2], linewidth=2, arrow_length_ratio=0.08)
    ax.text(
        config.axis_length + config.axis_label_offset,
        0,
        0,
        config.axis_labels[0],
        color=config.axis_colors[0],
        fontsize=config.axis_label_size,
        fontweight=config.axis_label_weight,
    )
    ax.text(
        0,
        config.axis_length + config.axis_label_offset,
        0,
        config.axis_labels[1],
        color=config.axis_colors[1],
        fontsize=config.axis_label_size,
        fontweight=config.axis_label_weight,
    )
    ax.text(
        0,
        0,
        config.axis_length + config.axis_label_offset,
        config.axis_labels[2],
        color=config.axis_colors[2],
        fontsize=config.axis_label_size,
        fontweight=config.axis_label_weight,
    )


def create_cartesian_figure(
    limit=10,
    view=DEFAULT_VIEW,
    corner_axes_config=DEFAULT_CORNER_AXES,
    center_object_config=DEFAULT_CENTER_OBJECT,
):
    # Create the figure and 3D axis, then set up the base scene and background axes
    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(111, projection="3d")
    setup_base_cartesian_scene(ax, limit, view)
    draw_background_axes(ax, limit)

    # Add reference axes in the back corner (e.g., ENU)
    add_corner_reference_axes(ax, limit, corner_axes_config)
    # Add the center cube and primary axes (e.g., XYZ)
    add_center_cube_with_axes(ax, center_object_config)

    return fig, ax


def main():
    parser = argparse.ArgumentParser(description="Draw a 3D Cartesian coordinate system.")
    parser.add_argument("--limit", type=float, default=10, help="Axis range limit.")
    args = parser.parse_args()

    create_cartesian_figure(limit=args.limit)
    plt.show()


if __name__ == "__main__":
    main()
