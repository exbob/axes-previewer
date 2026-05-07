# 设计：导出与 Apply 使用当前 3D 视角

**日期：** 2026-05-07  
**状态：** 设计已在对话中确认；实现以本文档为准  
**范围：** `scripts/cartesian_3d_gui.py` 及可选的 `scripts/cartesian_3d.py` 小工具函数  

## 1. 背景与问题

交互式 3D 预览（Matplotlib `Axes3D` + Tk）中，用户通过鼠标旋转调整视角。当前实现里 `self.view`（`view_config_t`）仅在应用启动时设为 `DEFAULT_VIEW`，之后不随交互更新。导出 PNG/SVG 时使用 `self.view` 在新 `Figure` 上重建场景，因此**始终对应初始默认相机**。用户期望：**导出图像与当前屏幕上调整后的视角一致**；且用户已确认 **Apply / redraw 也应保留当前视角**（仅重绘几何与标注，不重置相机）。

## 2. 目标与非目标

### 2.1 目标

- 导出 PNG/SVG 时，相机参数（至少 `elev` / `azim`，以及本环境 Matplotlib 可读到的投影相关参数）与**当前交互画布** `self.ax` 一致。
- 点击 **Apply / redraw** 后，**不改变**用户当前的 elev/azim（及与之一致的投影设置）。
- 与相机无关的 `view_config_t` 字段（如 `grid_alpha`、`box_aspect`）继续由 `self.view` 表示；本需求**不新增**专门 UI 修改这些字段。

### 2.2 非目标

- 不要求导出图与预览窗口在**像素级构图**完全一致（导出使用独立 `Figure` 尺寸与 DPI，纵横比差异可能导致取景框视觉略有不同）；要求**视角参数一致**。
- 不将「画布截图」作为 SVG 的交付方式（放弃矢量语义，不采纳）。

## 3. 方案结论

采用 **在会破坏或脱离当前轴状态的操作之前，从 `self.ax` 合并相机到 `view_config_t`**：

1. **`_redraw()`**：在 `self.ax.clear()` **之前**，根据 `self.ax` 更新 `self.view` 中与相机相关的字段，再按现有顺序 `clear` → `setup_base_cartesian_scene` → 绘制。
2. **`_export_png` / `_export_svg`**：在创建导出专用 `Figure` **之前**，同样从 `self.ax` 同步相机到用于本次导出的 `view_config_t`（可与 `self.view` 使用同一套同步逻辑，并写回 `self.view`，避免会话内状态长期漂移）。

**未采纳：** 仅靠鼠标事件持续写 `self.view`（易遗漏其它改相机路径，且导出前仍需从轴读取才稳妥）；**未采纳：** 以截屏替代矢量导出。

## 4. 数据流与职责

| 构件 | 职责 |
|------|------|
| `self.ax`（`Axes3D`） | 会话内用户旋转后的**相机真源**。 |
| `self.view`（`view_config_t`） | 传给 `cartesian_3d.setup_base_cartesian_scene` 的配置；在 `clear` 前与导出前通过同步函数从 `self.ax` 更新其**相机相关**字段。 |
| `cartesian_3d.py` | 保持「给定 `view_config_t` 即配置场景」；可选地将「从 `Axes3D` 抽取视角」提取为模块内小函数以便 GUI 与测试复用（非必须）。 |

## 5. 实现要点

### 5.1 同步函数（建议私有方法或模块级函数）

- 输入：目标 `Axes3D`（GUI 中为 `self.ax`）、当前 `self.view`（用于保留非相机字段及读不到时的回退）。
- 输出：新的 `view_config_t`（`dataclasses.replace`）。
- **至少**读取：`elev`、`azim`（与 `setup_base_cartesian_scene` 中 `view_init` 一致）。
- **投影：** 与 `view_config_t.proj_type`、`focal_length` 对齐；以运行时所依赖的 Matplotlib 版本**公开或稳定约定**的 API 为准；**若某字段无法从轴读取，则保留同步前 `self.view` 中该字段**，避免武断覆盖。
- **非相机字段**（`grid_alpha`、`box_aspect` 等）：保留 `self.view` 原值，除非将来另有 UI 写入。

### 5.2 调用点

- `_redraw()`：`clear()` 之前同步一次。
- `_export_png`、`_export_svg`：构建导出 `Figure` / `ax` 之前同步一次（覆盖「仅旋转、未点 Apply」仍要正确导出的场景）；若与 `_redraw` 共用逻辑并写回 `self.view`，则两处行为一致。

### 5.3 首次绘制

应用 `__init__` 末尾已有 `_redraw()`；首次同步从已按 `DEFAULT_VIEW` 初始化的轴读取，应与默认视角一致或等价，不应引入异常。

## 6. 测试与验收

- **手工验收（必须）：**  
  - 旋转画布 → 导出 PNG/SVG → 确认与屏上视角一致（在合理容差内）。  
  - 旋转 → **Apply / redraw** → 确认视角未跳回默认。  
  - 旋转 → Apply → 再导出 → 仍一致。  
- **自动化：** 本 spec 不强制；若后续补充，需评估 Matplotlib 无头环境与版本差异。

## 7. 风险与说明

- Matplotlib 大版本间 3D 投影实现细节可能不同；实现阶段应在本仓库声明或锁定的 Python/Matplotlib 版本上验证。
- 导出图与预览窗口比例不同时，**边缘留白与 `bbox_inches='tight'` 裁剪**可能不同；不视为本需求的缺陷，除非后续单独提「构图对齐」需求。

## 8. 后续步骤

实现前：由实现侧按 **writing-plans** 产出实现计划，再编码。本文档经书面确认后视为 spec 基线。
