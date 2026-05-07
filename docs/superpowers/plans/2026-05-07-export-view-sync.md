# Export / Apply 视角同步 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 导出 PNG/SVG 与点击 Apply / redraw 时均使用当前交互画布上的 3D 相机（elev/azim 及可恢复的投影参数），而不是始终使用启动时的默认 `view_config_t`。

**Architecture:** 在 `cartesian_3d.py` 增加纯函数 `view_config_from_3d_axes(ax, base)`，从 `Axes3D` 读取相机相关字段并与 `base` 合并。GUI 在「已至少成功绘制过一次场景」之后，于 `_redraw()` 的 `clear()` 之前及导出路径开头调用该函数更新 `self.view`；首次绘制前不同步，避免把 Matplotlib 子图初始默认 azim 等写回 `self.view` 覆盖仓库默认值。

**Tech stack:** Python 3、`matplotlib`（`mpl_toolkits.mplot3d`）、Tk、`dataclasses.replace`；测试使用 `pytest` 与 `matplotlib` Agg 后端（无显示器）。

---

## 文件与职责

| 文件 | 职责 |
|------|------|
| `scripts/cartesian_3d.py` | 新增 `view_config_from_3d_axes()`；文档字符串说明参数、返回值与对 `_focal_length` 的依赖（Matplotlib 内部属性，读不到则仅更新 elev/azim）。 |
| `scripts/cartesian_3d_gui.py` | 增加 `_scene_ready` 标志；`_sync_view_from_interactive_ax()`；在 `_redraw` / `_export_png` / `_export_svg` 中按 spec 调用。 |
| `scripts/requirements-dev.txt`（新建） | 开发依赖：`pytest`、`matplotlib`（与运行一致；若已有全局可省略安装 matplotlib）。 |
| `tests/test_view_config_from_3d_axes.py`（新建） | 覆盖同步函数在 persp / ortho（若可设）及缺省 `_focal_length` 时的行为。 |

---

### Task 1: `view_config_from_3d_axes` 与单元测试

**Files:**

- Create: `scripts/requirements-dev.txt`
- Create: `tests/test_view_config_from_3d_axes.py`
- Modify: `scripts/cartesian_3d.py`（在 `setup_base_cartesian_scene` 之前插入新函数与 `import math`）

- [ ] **Step 1: 新建开发依赖清单**

Create `scripts/requirements-dev.txt`:

```text
matplotlib
pytest
```

- [ ] **Step 2: 在 `cartesian_3d.py` 顶部增加 `import math`**

在现有 `from dataclasses import dataclass` 同一区域加入：

```python
import math
```

- [ ] **Step 3: 在 `setup_base_cartesian_scene` 定义之前加入新函数**

在 `def setup_base_cartesian_scene(ax, limit, view):` 之前插入：

```python
def view_config_from_3d_axes(ax, base: view_config_t) -> view_config_t:
    """
    Merge camera-related fields from a live Axes3D into a view_config_t.

    Non-camera fields (grid_alpha, box_aspect, etc.) are taken from base.
    If perspective focal length cannot be read from the axis, proj_type and
    focal_length fall back to base.

    Args:
        ax: Matplotlib Axes3D instance.
        base: Existing view configuration (provides defaults and non-camera fields).

    Returns:
        New view_config_t with elev/azim from ax and best-effort projection fields.
    """
    elev = float(ax.elev)
    azim = float(ax.azim)
    fl_attr = getattr(ax, "_focal_length", None)
    if fl_attr is None:
        return replace(base, elev=elev, azim=azim)
    try:
        fl_float = float(fl_attr)
    except (TypeError, ValueError):
        return replace(base, elev=elev, azim=azim)
    if math.isinf(fl_float):
        return replace(base, elev=elev, azim=azim, proj_type="ortho")
    return replace(base, elev=elev, azim=azim, proj_type="persp", focal_length=fl_float)
```

并在文件顶部已有 `from dataclasses import dataclass` 处补充：

```python
from dataclasses import dataclass, replace
```

（若已有 `replace` 则勿重复。）

- [ ] **Step 4: 编写失败测试（先写测试再实现函数体时，可先跑通 Step 3 再跑测试；此处顺序为 TDD：若 Step 3 已写完整函数，本步为验证测试通过）**

Create `tests/test_view_config_from_3d_axes.py`:

```python
import sys
from pathlib import Path

import matplotlib
import pytest

matplotlib.use("Agg")
import matplotlib.pyplot as plt

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
```

- [ ] **Step 5: 运行测试**

Run:

```bash
cd /home/lsc/workspace/axes-previewer
python3 -m venv .venv
.venv/bin/pip install -r scripts/requirements-dev.txt
.venv/bin/python -m pytest tests/test_view_config_from_3d_axes.py -v
```

Expected: 全部 PASS。

- [ ] **Step 6: Commit**

```bash
git add scripts/cartesian_3d.py scripts/requirements-dev.txt tests/test_view_config_from_3d_axes.py
git commit -m "feat(cartesian_3d): add view_config_from_3d_axes helper

Derive view_config_t camera fields from Axes3D for GUI sync; add pytest coverage."
```

---

### Task 2: GUI 同步与 `_scene_ready` 门闩

**Files:**

- Modify: `scripts/cartesian_3d_gui.py`（`Cartesian3DEditorApp.__init__`、`_redraw`、`_export_png`、`_export_svg`）

- [ ] **Step 1: 在 `__init__` 中初始化标志**

在 `self.view = c3d.DEFAULT_VIEW` 之后增加：

```python
        self._scene_ready = False
```

- [ ] **Step 2: 增加同步方法**

在 `Cartesian3DEditorApp` 内、`_redraw` 之前添加：

```python
    def _sync_view_from_interactive_ax(self) -> None:
        if not self._scene_ready:
            return
        self.view = c3d.view_config_from_3d_axes(self.ax, self.view)
```

- [ ] **Step 3: 修改 `_redraw`**

在 `try:` 块内、`self.ax.clear()` **之前**插入：

```python
            self._sync_view_from_interactive_ax()
```

在 `self.canvas.draw()` 成功执行之后（仍在 try 内、紧接 draw），设置：

```python
            self._scene_ready = True
```

若 `draw` 前抛错，不应将 `_scene_ready` 置为 True（保持现有 `except` 分支不设置即可）。

- [ ] **Step 4: 修改 `_export_png` 与 `_export_svg`**

在两个函数中，在 `state = self._collect_state()` 之后、校验 center/corner 之前或之后均可，但在 `Figure(...)` 创建 **之前** 增加：

```python
        self._sync_view_from_interactive_ax()
```

若 `_scene_ready` 仍为 False（理论上仅发生在导出极早调用），同步函数为空操作，导出仍用 `self.view`，与当前行为一致。

- [ ] **Step 5: 手工验收（必须）**

1. `python3 scripts/cartesian_3d_gui.py`（或项目文档中的启动方式）启动 GUI。  
2. 旋转 3D 视图 → 导出 PNG → 打开文件，视角应与窗口一致。  
3. 旋转 → 导出 SVG → 用浏览器或 Inkscape 打开，视角一致。  
4. 旋转 → 点击 Apply / redraw → 视角应保持，不应跳回默认。  
5. 启动后不改视角直接导出 → 应与默认 `view_config_t` 一致（回归）。

- [ ] **Step 6: Commit**

```bash
git add scripts/cartesian_3d_gui.py
git commit -m "fix(gui): sync view_config from Axes3D before redraw and export

Preserve user camera for Apply and PNG/SVG export; skip sync until first
successful scene draw."
```

---

### Task 3: 文档与收尾（可选但建议）

**Files:**

- Modify: `README.md`（若其中有「导出」或 GUI 行为描述）

- [ ] **Step 1: 在 README 的 GUI 小节用一两句话说明：导出与 Apply 使用当前视角；开发测试可安装 `scripts/requirements-dev.txt`。**

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: note export and apply use current 3D view"
```

---

## Plan self-review

**1. Spec coverage**

| Spec 要求 | 对应任务 |
|-----------|----------|
| 导出使用当前 `self.ax` 相机 | Task 2 `_export_*` 中 `_sync_view_from_interactive_ax` |
| Apply 保留视角 | Task 2 `_redraw` 中 clear 前同步 + `_scene_ready` |
| 非相机字段保留在 `self.view` | Task 1 `view_config_from_3d_axes` 使用 `replace(..., base)` |
| 读不到的投影字段回退 base | Task 1 `_focal_length` 缺失分支 |
| 手工验收 | Task 2 Step 5 |

**2. Placeholder scan** — 无 TBD/TODO。

**3. Type / 命名一致性** — `view_config_from_3d_axes` / `_sync_view_from_interactive_ax` / `_scene_ready` 在全计划一致。

---

**Plan complete and saved to `docs/superpowers/plans/2026-05-07-export-view-sync.md`. Two execution options:**

**1. Subagent-Driven（推荐）** — 每个 Task 派生子代理、任务间评审、迭代快  

**2. Inline Execution** — 在本会话用 executing-plans 按检查点批量执行  

**你想用哪一种？**
