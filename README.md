# axes-previewer

## 项目介绍

这是一个 Python 小工具，用于预览 ENU 参考坐标系（East-North-Up）中，符合右手定则的物体的坐标轴方向，适合用于坐标系方向展示、教学演示和视觉化验证。

参考坐标系中，空间方位与 ENU 方向的对应关系：

| 方位 | 方向 |
|---|---|
| 前 (Front) | 北 (North) |
| 后 (Back)  | 南 (South) |
| 右 (Right) | 东 (East)  |
| 左 (Left)  | 西 (West)  |
| 上 (Up)    | 天 (Zenith/Up)  |
| 下 (Down)  | 地 (Nadir/Down) |

运行后会显示三维场景，包含以下效果：

- 带网格与刻度的三维坐标空间
- 背景空间方位标注：`up/down/front/back/left/right`
- 角落有 ENU 坐标系的参考轴（`E/N/U`）
- 原点处的半透明立方体，带有 `X/Y/Z` 三个坐标轴指向，符合右手坐标系。
- 立方体面文字，用于标识物体名称（可配置文字内容、显示面、沿轴方向）
- 立方体面黑色圆点，用于标识芯片的 Pin1 引脚位置（可配置显示面和角位，贴在表面）

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

### 软件模块划分

这个软件可以分为 3 个核心部分：

1. **3D 空间网格与背景方位轴**  
   用于提供整体空间参照，包括网格、刻度和六个方位背景坐标轴（`up/down/front/back/left/right`）。
2. **角落 ENU 参考坐标轴（负方向角）**  
   用于显示 ENU（`E/N/U`）参考方向，默认放置在坐标系负方向角，帮助对照空间方位与工程坐标语义。
3. **中间立方体对象**  
   作为被标识物体，包含多个可自定义属性：
   - 立方体面文字：用于标识物体名称和正面方向；
   - 立方体面圆点：用于标识芯片 `Pin1` 引脚位置；
   - 立方体坐标轴：用于标识物体 `X/Y/Z` 轴指向（支持右手系约束校验）。

### 对应配置结构

上述 3 个部分分别由以下配置数据结构驱动（均为 `@dataclass(frozen=True)`）：

- `view_config_t`：控制 3D 空间网格与视角（网格透明度、投影、相机角度等）。
- `corner_axes_config_t`：控制角落 ENU 参考坐标轴（长度、偏移、标签等）。
- `center_object_config_t`：控制中间立方体及其可自定义属性（面文字、圆点、`X/Y/Z` 轴方向等）。

其中，`center_object_config_t.axis_directions` 会通过 `_validate_and_get_axis_vectors()` 校验是否满足右手坐标系（`X × Y = Z`）。

### 运行逻辑

整体调用顺序如下：

1. `main()` 解析参数（`--limit`、`--output`、`--dpi`）。
2. `main()` 调用 `create_cartesian_figure()` 创建绘图对象。
3. `create_cartesian_figure()` 依次绘制：
   - 3D 空间网格与背景方位轴；
   - 角落 ENU 参考坐标轴；
   - 中间立方体（含面文字、圆点和 `X/Y/Z` 轴）。
4. 若指定 `--output` 则导出图片，否则调用 `plt.show()` 交互显示。

对应流程图：

```mermaid
flowchart TD
	A[main() 启动] --> B[解析参数]
	B --> C[create_cartesian_figure()]
	C --> D[绘制3D空间网格与六方位背景轴]
	D --> E[绘制右下角ENU参考坐标轴]
	E --> F[绘制中间立方体]
	F --> G[绘制面文字]
	F --> H[绘制Pin1圆点]
	F --> I[校验并绘制X/Y/Z轴方向]
	I --> J{通过右手系校验?}
	J -- 否 --> K[抛出 ValueError]
	J -- 是 --> L{是否指定 --output?}
	L -- 是 --> M[导出 .png/.svg]
	L -- 否 --> N[plt.show() 交互显示]
```

### 如何修改中间立方体三轴箭头指向（保持右手系）

在 `center_object_config_t` 中使用 `axis_directions` 配置 `X/Y/Z` 三个箭头指向，支持：

- `right/left`
- `front/back`
- `up/down`

默认值：

```python
axis_directions: tuple = ("right", "front", "up")
```

例如你提到的映射：

```python
axis_directions: tuple = ("left", "front", "down")
```

该映射满足右手系（`X × Y = Z`），因此是合法的。程序会自动校验：

- 必须恰好提供 3 个方向（对应 `X/Y/Z`）
- 三个方向不能重复
- 必须构成右手坐标系，否则抛出错误

### 如何修改立方体面的文字

这个文字用于标识物体的名称和正面的位置。

在 `cartesian_3d.py` 中，`center_object_config_t` 提供了贴在立方体表面的文字配置：

```python
@dataclass(frozen=True)
class center_object_config_t:
    # ...
    face_text: str = "Sensor"      # 文字内容
    face_name: str = "up"          # 显示面: up/down/front/back/left/right
    face_text_axis: str = "x"      # 文字沿面内哪个轴方向显示，支持 x/y/z 与 -x/-y/-z
    face_text_color: str = "k"     # 文字颜色
    face_text_size: float = 0.8    # 文字大小
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

如果立方体是一个芯片，这个圆点用于标识芯片的 Pin1 引脚位置。在 `center_object_config_t` 中使用以下字段控制黑色圆点：

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
