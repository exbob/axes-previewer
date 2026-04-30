#!/usr/bin/env python3
import argparse

import matplotlib.pyplot as plt


def create_cartesian_figure(limit=10):
    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(111, projection="3d")

    ax.set_xlim(-limit, limit)
    ax.set_ylim(-limit, limit)
    ax.set_zlim(-limit, limit)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.set_title("3D Cartesian Coordinate System")
    ax.grid(True)
    ax.set_box_aspect((1, 1, 1))

    ax.quiver(0, 0, 0, limit, 0, 0, color="r", linewidth=2, arrow_length_ratio=0.08)
    ax.quiver(0, 0, 0, 0, limit, 0, color="g", linewidth=2, arrow_length_ratio=0.08)
    ax.quiver(0, 0, 0, 0, 0, limit, color="b", linewidth=2, arrow_length_ratio=0.08)
    ax.scatter(0, 0, 0, color="k", s=60, marker="o")

    ax.text(limit, 0, 0, "X", color="r")
    ax.text(0, limit, 0, "Y", color="g")
    ax.text(0, 0, limit, "Z", color="b")

    return fig, ax


def main():
    parser = argparse.ArgumentParser(description="Draw a 3D Cartesian coordinate system.")
    parser.add_argument("--limit", type=float, default=10, help="Axis range limit.")
    args = parser.parse_args()

    create_cartesian_figure(limit=args.limit)
    plt.show()


if __name__ == "__main__":
    main()
