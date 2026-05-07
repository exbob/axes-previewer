import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pytest

_SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(_SCRIPTS))

import cartesian_3d as c3d


def test_view_config_from_axes_persp_matches_focal():
    base = c3d.view_config_t(azim=-20, focal_length=0.65)
    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")
    ax.view_init(elev=12.5, azim=77.0)
    ax.set_proj_type("persp", focal_length=0.88)
    out = c3d.view_config_from_3d_axes(ax, base)
    assert out.elev == pytest.approx(12.5)
    assert out.azim == pytest.approx(77.0)
    assert out.proj_type == "persp"
    assert out.focal_length == pytest.approx(0.88)
    assert out.grid_alpha == base.grid_alpha
    assert out.box_aspect == base.box_aspect
    plt.close(fig)


def test_view_config_from_axes_ortho():
    base = c3d.view_config_t()
    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")
    ax.view_init(elev=5.0, azim=-40.0)
    ax.set_proj_type("ortho")
    out = c3d.view_config_from_3d_axes(ax, base)
    assert out.elev == pytest.approx(5.0)
    assert out.azim == pytest.approx(-40.0)
    assert out.proj_type == "ortho"
    plt.close(fig)


def test_view_config_from_axes_preserves_base_when_no_focal_attr():
    base = c3d.view_config_t(elev=30, azim=-20, proj_type="persp", focal_length=0.65)

    class FakeAx:
        elev = 1.0
        azim = 2.0

    out = c3d.view_config_from_3d_axes(FakeAx(), base)
    assert out.elev == 1.0
    assert out.azim == 2.0
    assert out.proj_type == base.proj_type
    assert out.focal_length == base.focal_length
