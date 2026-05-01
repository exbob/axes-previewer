# axes-previewer

## 项目介绍

这是一个用于预览 3D 笛卡尔坐标系的 Python 小工具，适合用于坐标系方向展示、教学演示和视觉化验证。

运行后会显示三维场景，包含以下效果：

- 带网格与刻度的三维坐标空间
- 原点处的半透明立方体
- 中心主轴（`X/Y/Z`）
- 角落参考轴（默认 `E/N/U`）

## 使用方法

### 依赖安装

建议先创建并启用虚拟环境：

```bash
python3 -m venv .venv
source .venv/bin/activate
```

安装依赖：

```bash
python3 -m pip install -r requirements.txt
```

### 运行命令

在项目根目录执行：

```bash
python3 cartesian_3d.py
```

### 参数说明

- `--limit`：坐标轴范围上限（浮点数），默认值 `10`

示例：

```bash
python3 cartesian_3d.py --limit 12
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
