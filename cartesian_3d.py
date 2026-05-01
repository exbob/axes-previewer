#!/usr/bin/env python3
import argparse
from pathlib import Path
from dataclasses import dataclass

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, PathPatch
from matplotlib.ticker import MultipleLocator
from matplotlib.textpath import TextPath
from matplotlib.transforms import Affine2D
from mpl_toolkits.mplot3d import art3d
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


@dataclass(frozen=True)
class view_config_t:
    elev: float = 30
    azim: float = -20
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
    cube_size: float = 6
    cube_color: str = "green"
    cube_alpha: float = 0.20
    axis_length: float = 7
    axis_colors: tuple = ("r", "y", "b")
    axis_labels: tuple = ("X", "Y", "Z")
    axis_directions: tuple = ("right", "front", "up")
    axis_label_size: float = 16
    axis_label_weight: str = "bold"
    axis_label_offset: float = 0.2
    face_text: str = "Sensor"
    face_name: str = "up"
    face_text_axis: str = "x"
    face_text_color: str = "k"
    face_text_size: float = 0.8
    face_dot_enabled: bool = True
    face_dot_name: str = "up"
    face_dot_corner: str = "left_top"
    face_dot_radius: float = 0.12
    face_dot_edge_offset: float = 0.5


DEFAULT_VIEW = view_config_t()
DEFAULT_CORNER_AXES = corner_axes_config_t()
DEFAULT_CENTER_OBJECT = center_object_config_t()


_DIRECTION_TO_VECTOR = {
    "right": (1, 0, 0),
    "left": (-1, 0, 0),
    "front": (0, 1, 0),
    "back": (0, -1, 0),
    "up": (0, 0, 1),
    "down": (0, 0, -1),
}


def _dot_product(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross_product(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _validate_and_get_axis_vectors(axis_directions):
    """
    Validate X/Y/Z axis direction mapping and return unit vectors.

    Args:
        axis_directions: A 3-item tuple for X/Y/Z axis directions.
            Supported values are
            {"right", "left", "front", "back", "up", "down"}.

    Returns:
        A list of 3 tuples, each being a Cartesian unit vector.

    Raises:
        ValueError: If direction count is not 3, values are duplicated/unsupported,
            or the mapping does not satisfy right-handed rule (X x Y = Z).
    """
    if len(axis_directions) != 3:
        raise ValueError("axis_directions must contain exactly 3 directions for X/Y/Z")
    if len(set(axis_directions)) != 3:
        raise ValueError("axis_directions for X/Y/Z must be unique")

    vectors = []
    for direction in axis_directions:
        if direction not in _DIRECTION_TO_VECTOR:
            raise ValueError(
                "Unsupported axis direction: "
                f"{direction}. Must be one of {tuple(_DIRECTION_TO_VECTOR.keys())}"
            )
        vectors.append(_DIRECTION_TO_VECTOR[direction])

    x_vec, y_vec, z_vec = vectors
    if _dot_product(_cross_product(x_vec, y_vec), z_vec) != 1:
        raise ValueError(
            "axis_directions must form a right-handed coordinate system (X x Y = Z)"
        )
    return vectors


def setup_base_cartesian_scene(ax, limit, view):
    """
    Configure base 3D scene with limits, labels, ticks, and camera.

    Args:
        ax: Target 3D axis.
        limit: Axis range limit in all three dimensions.
        view: View configuration object controlling projection and camera.
    """
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
    """
    Draw dashed global XYZ axes and six-direction background labels.

    Args:
        ax: Target 3D axis.
        limit: Axis range limit used for line and label placement.
    """
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
    """
    Draw reference axes (default ENU labels) at the negative corner.

    Args:
        ax: Target 3D axis.
        limit: Axis range limit used to compute corner origin.
        config: Corner reference-axis drawing configuration.
    """
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
    """
    Draw center cube, object XYZ axes, and optional face markers.

    This function renders:
        1) Semi-transparent cube at origin
        2) Face text marker (object name/front direction)
        3) Optional face dot marker (e.g., chip Pin1)
        4) Object XYZ axes based on configured direction mapping

    Args:
        ax: Target 3D axis.
        config: Center object configuration including cube style, axis labels/colors,
            axis direction mapping, face text, and face dot options.

    Raises:
        ValueError: Propagated from axis direction and face marker validation.
    """
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
    add_text_on_cube_face(
        ax=ax,
        cube_half=half,
        text=config.face_text,
        face=config.face_name,
        axis=config.face_text_axis,
        color=config.face_text_color,
        size=config.face_text_size,
    )
    if config.face_dot_enabled:
        add_dot_on_cube_face(
            ax=ax,
            cube_half=half,
            face=config.face_dot_name,
            corner=config.face_dot_corner,
            edge_offset=config.face_dot_edge_offset,
            radius=config.face_dot_radius,
        )

    axis_vectors = _validate_and_get_axis_vectors(config.axis_directions)
    for index, vector in enumerate(axis_vectors):
        dx = vector[0] * config.axis_length
        dy = vector[1] * config.axis_length
        dz = vector[2] * config.axis_length
        ax.quiver(
            0,
            0,
            0,
            dx,
            dy,
            dz,
            color=config.axis_colors[index],
            linewidth=2,
            arrow_length_ratio=0.08,
        )
        label_scale = config.axis_length + config.axis_label_offset
        ax.text(
            vector[0] * label_scale,
            vector[1] * label_scale,
            vector[2] * label_scale,
            config.axis_labels[index],
            color=config.axis_colors[index],
            fontsize=config.axis_label_size,
            fontweight=config.axis_label_weight,
        )


def add_text_on_cube_face(ax, cube_half, text, face, axis, color="k", size=0.9):
    """
    Add text as a 2D path patch projected onto a specific cube face.

    Args:
        ax: Target 3D axis.
        cube_half: Half of cube size.
        text: Text content to display.
        face: Target face name, one of
            {"up", "down", "front", "back", "left", "right"}.
        axis: In-face text direction axis.
            Supports positive/negative form such as "x" and "-x".
        color: Text fill color.
        size: Text path size.

    Raises:
        ValueError: If face is unsupported or axis does not belong to the face.
    """
    face_to_plane = {
        "up": ("z", cube_half + 0.001),
        "down": ("z", -cube_half - 0.001),
        "front": ("y", cube_half + 0.001),
        "back": ("y", -cube_half - 0.001),
        "right": ("x", cube_half + 0.001),
        "left": ("x", -cube_half - 0.001),
    }
    plane_axis_rotation = {
        "z": {"x": 0, "y": 90},
        "y": {"x": 0, "z": 90},
        "x": {"y": 0, "z": 90},
    }
    if face not in face_to_plane:
        raise ValueError(f"Unsupported face: {face}")

    zdir, z_value = face_to_plane[face]
    axis_rotation = plane_axis_rotation[zdir]
    axis_sign = 1
    axis_name = axis
    if axis.startswith("-"):
        axis_sign = -1
        axis_name = axis[1:]
    if axis_name not in axis_rotation:
        raise ValueError(f"Axis '{axis}' is not on face '{face}'")
    rotation_deg = axis_rotation[axis_name]
    if axis_sign < 0:
        rotation_deg += 180

    text_path = TextPath((0, 0), text, size=size)
    bbox = text_path.get_extents()
    text_transform = (
        Affine2D()
        .translate(-(bbox.x0 + bbox.width / 2), -(bbox.y0 + bbox.height / 2))
        .rotate_deg(rotation_deg)
    )
    text_patch = PathPatch(
        text_transform.transform_path(text_path),
        facecolor=color,
        edgecolor="none",
        alpha=1.0,
    )
    ax.add_patch(text_patch)
    art3d.pathpatch_2d_to_3d(text_patch, z=z_value, zdir=zdir)


def add_dot_on_cube_face(ax, cube_half, face, corner, edge_offset=0.5, radius=0.12):
    """Add a black dot on a cube face at a corner-offset position."""
    face_plane = {
        "up": ("z", cube_half + 0.001),
        "down": ("z", -cube_half - 0.001),
        "front": ("y", cube_half + 0.001),
        "back": ("y", -cube_half - 0.001),
        "right": ("x", cube_half + 0.001),
        "left": ("x", -cube_half - 0.001),
    }
    corner_aliases = {
        "left_top": "left_top",
        "left_bottom": "left_bottom",
        "right_top": "right_top",
        "right_bottom": "right_bottom",
    }
    corner_to_xy = {
        "left_top": (-cube_half + edge_offset, cube_half - edge_offset),
        "left_bottom": (-cube_half + edge_offset, -cube_half + edge_offset),
        "right_top": (cube_half - edge_offset, cube_half - edge_offset),
        "right_bottom": (cube_half - edge_offset, -cube_half + edge_offset),
    }
    if face not in face_plane:
        raise ValueError(f"Unsupported face: {face}")
    if corner not in corner_aliases:
        raise ValueError(f"Unsupported corner: {corner}")
    if not (0 <= edge_offset <= cube_half):
        raise ValueError("edge_offset must satisfy 0 <= edge_offset <= cube_half")

    dot_x, dot_y = corner_to_xy[corner_aliases[corner]]
    dot_patch = Circle((dot_x, dot_y), radius=radius, facecolor="k", edgecolor="none", alpha=1.0)
    ax.add_patch(dot_patch)
    zdir, z_value = face_plane[face]
    art3d.pathpatch_2d_to_3d(dot_patch, z=z_value, zdir=zdir)


def create_cartesian_figure(
    limit=10,
    view=DEFAULT_VIEW,
    corner_axes_config=DEFAULT_CORNER_AXES,
    center_object_config=DEFAULT_CENTER_OBJECT,
):
    """
    Build the full Cartesian preview figure and return figure handles.

    Args:
        limit: Axis range limit in world coordinates.
        view: Scene/camera configuration.
        corner_axes_config: Reference corner-axis configuration.
        center_object_config: Center cube and primary-axis configuration.

    Returns:
        A tuple (fig, ax) where fig is matplotlib Figure and ax is 3D axis.
    """
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
    """
    Parse CLI arguments, render figure, and show or export image.

    Raises:
        SystemExit: Raised by argparse on invalid CLI arguments.
    """
    parser = argparse.ArgumentParser(description="Draw a 3D Cartesian coordinate system.")
    parser.add_argument("--limit", type=float, default=10, help="Axis range limit.")
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path. Supports .png or .svg; if omitted, show interactive window.",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=100,
        help="PNG export DPI (default: 100). Only used when --output is .png.",
    )
    args = parser.parse_args()
    if args.dpi <= 0:
        parser.error("--dpi must be a positive integer")

    fig, _ = create_cartesian_figure(limit=args.limit)
    if args.output:
        output_path = Path(args.output)
        output_ext = output_path.suffix.lower()
        if output_ext not in {".png", ".svg"}:
            parser.error("--output only supports .png or .svg file extension")
        if output_ext == ".png":
            fig.savefig(output_path, format="png", dpi=args.dpi, bbox_inches="tight")
        else:
            fig.savefig(output_path, format="svg", bbox_inches="tight")
        plt.close(fig)
    else:
        plt.show()


if __name__ == "__main__":
    main()
