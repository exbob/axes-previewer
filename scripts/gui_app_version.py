"""
Resolve application version for the Cartesian 3D GUI.

Prefers a bundled ``app_version.txt`` (written at CI/build time), then
``git describe --tags --always --long`` from the scripts directory, else
``unknown``.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def get_app_version(scripts_dir: Path) -> str:
    """
    Return a version string for display and release metadata.

    scripts_dir: directory containing ``cartesian_3d_gui.py`` and optional
        ``app_version.txt``.
    Returns non-empty version string, or ``unknown`` if unresolved.
    """
    text = _read_bundled_version(scripts_dir)
    if text is not None:
        return text
    text = _version_from_git(scripts_dir)
    if text is not None:
        return text
    return "unknown"


def _read_bundled_version(scripts_dir: Path) -> str | None:
    candidates: list[Path] = []
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        candidates.append(Path(sys._MEIPASS) / "app_version.txt")
    candidates.append(scripts_dir / "app_version.txt")
    for path in candidates:
        line = _read_version_file(path)
        if line is not None:
            return line
    return None


def _read_version_file(path: Path) -> str | None:
    try:
        raw = path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return raw if raw else None


def _version_from_git(scripts_dir: Path) -> str | None:
    try:
        proc = subprocess.run(
            [
                "git",
                "-C",
                str(scripts_dir),
                "describe",
                "--tags",
                "--always",
                "--long",
            ],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    line = proc.stdout.strip()
    return line if line else None
