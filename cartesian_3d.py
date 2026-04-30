#!/usr/bin/env python3
import argparse

import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator


TEACHING_VIEW = {
    "elev": 20,
    "azim": -50,
    "proj_type": "persp",
    "focal_length": 0.65,
    "grid_alpha": 0.35,
    "box_aspect": (1, 1, 1),
}


def create_cartesian_figure(limit=10):
    view = TEACHING_VIEW
    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(111, projection="3d")

    ax.set_xlim(-limit, limit)
    ax.set_ylim(-limit, limit)
    ax.set_zlim(-limit, limit)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.set_title("3D Cartesian Coordinate System")
    ax.grid(True, alpha=view["grid_alpha"])
    ax.set_box_aspect(view["box_aspect"])
    ax.xaxis.set_major_locator(MultipleLocator(2))
    ax.yaxis.set_major_locator(MultipleLocator(2))
    ax.zaxis.set_major_locator(MultipleLocator(2))
    ax.view_init(elev=view["elev"], azim=view["azim"])
    if view["proj_type"] == "persp":
        ax.set_proj_type("persp", focal_length=view["focal_length"])
    else:
        ax.set_proj_type("ortho")

    # Background right-handed Cartesian axes (negative and positive directions).
    ax.plot([-limit, limit], [0, 0], [0, 0], color="0.35", linestyle="--", linewidth=1.4)
    ax.plot([0, 0], [-limit, limit], [0, 0], color="0.35", linestyle="--", linewidth=1.4)
    ax.plot([0, 0], [0, 0], [-limit, limit], color="0.35", linestyle="--", linewidth=1.4)
    # Direction labels on the background axes.
    label_offset = limit * 1.05
    ax.text(label_offset, 0, 0, "Right", color="0.35")
    ax.text(-label_offset, 0, 0, "Left", color="0.35")
    ax.text(0, label_offset, 0, "Front", color="0.35")
    ax.text(0, -label_offset, 0, "Back", color="0.35")
    ax.text(0, 0, label_offset, "Up", color="0.35")
    ax.text(0, 0, -label_offset, "Down", color="0.35")

    return fig, ax


def main():
    parser = argparse.ArgumentParser(description="Draw a 3D Cartesian coordinate system.")
    parser.add_argument("--limit", type=float, default=10, help="Axis range limit.")
    args = parser.parse_args()

    create_cartesian_figure(limit=args.limit)
    plt.show()


if __name__ == "__main__":
    main()
