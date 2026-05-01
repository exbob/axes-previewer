# axes-previewer

## 项目介绍

这是一个用于预览 3D 笛卡尔坐标系的 Python 小工具，适合用于坐标系方向展示、教学演示和视觉化验证。

运行后会显示三维场景，包含以下效果：

- 带网格与刻度的三维坐标空间
- 中心主轴（`X/Y/Z`）
- 角落参考轴（默认 `E/N/U`）
- 原点处的半透明立方体
- 立方体面文字（可配置文字内容、显示的面和沿轴方向）
- 立方体面黑色圆点（可配置显示面和角位，贴在表面）

## 使用方法

建议先创建并启用虚拟环境：

```bash
python3 -m venv .venv
source .venv/bin/activate
```

安装依赖：

```bash
python3 -m pip install -r requirements.txt
```

在项目根目录执行：

```bash
python3 cartesian_3d.py
```

参数说明：

- `--limit`：坐标轴范围上限（浮点数），默认值 `10`
- `--output`：导出图片文件路径，支持 `.png` 或 `.svg`；传该参数时不会弹出交互窗口
- `--dpi`：导出 PNG 的分辨率（整数，默认 `100`）；仅在 `--output` 为 `.png` 时生效

示例：

```bash
python3 cartesian_3d.py --limit 12
```

```bash
python3 cartesian_3d.py --output preview.png
python3 cartesian_3d.py --output preview.png --dpi 300
python3 cartesian_3d.py --limit 12 --output preview.svg
```

## 开发说明

### 如何修改中间立方体的坐标轴标识

在 `cartesian_3d.py` 中找到 `center_object_config_t`，修改 `axis_labels` 字段即可：

```python
@dataclass(frozen=True)
class center_object_config_t:
    # ...
    axis_labels: tuple = ("X", "Y", "Z")
```

通常只需要调整 `X/Y/Z` 的顺序，例如改为 `Y/X/Z`：

```python
axis_labels: tuple = ("Y", "X", "Z")
```

### 如何修改立方体面的文字

在 `cartesian_3d.py` 中，`center_object_config_t` 提供了贴在立方体表面的文字配置：

```python
@dataclass(frozen=True)
class center_object_config_t:
    # ...
    face_text: str = "sensor"      # 文字内容
    face_name: str = "up"          # 显示面: up/down/front/back/left/right
    face_text_axis: str = "x"      # 文字沿面内哪个轴方向显示，支持 x/y/z 与 -x/-y/-z
    face_text_color: str = "k"     # 文字颜色
    face_text_size: float = 0.9    # 文字大小
```

`face_text_axis` 必须是当前 `face_name` 所在平面内的轴，不能使用该面的法向轴。合法组合如下：

- `face_name = "up"` 或 `"down"`：`face_text_axis` 只能是 `x/-x/y/-y`（不能是 `z/-z`）
- `face_name = "front"` 或 `"back"`：`face_text_axis` 只能是 `x/-x/z/-z`（不能是 `y/-y`）
- `face_name = "left"` 或 `"right"`：`face_text_axis` 只能是 `y/-y/z/-z`（不能是 `x/-x`）

示例：把文字改为 `camera`，显示在 `front` 面，并沿 `z` 轴方向排布：

```python
face_text: str = "camera"
face_name: str = "front"
face_text_axis: str = "z"
```

如果要验证沿 X 轴负方向显示，可改为：

```python
face_text_axis: str = "-x"
```

### 如何配置立方体面的黑色圆点

在 `center_object_config_t` 中使用以下字段控制黑色圆点：

```python
@dataclass(frozen=True)
class center_object_config_t:
    # ...
    face_dot_enabled: bool = True        # 是否显示圆点
    face_dot_name: str = "up"            # 显示面: up/down/front/back/left/right
    face_dot_corner: str = "left_top"    # 角位: left_top/left_bottom/right_top/right_bottom
    face_dot_radius: float = 0.12        # 圆点半径
    face_dot_edge_offset: float = 0.5    # 距离所选角两条边的固定距离
```

说明：

- `face_dot_corner` 目前只支持英文值：`left_top`、`left_bottom`、`right_top`、`right_bottom`
- `face_dot_edge_offset` 默认 `0.5`，表示圆点到所选角两条边的距离都为 `0.5`
