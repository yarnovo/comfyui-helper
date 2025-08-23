# 精灵图合成示例

这个示例演示如何使用精灵图合成工具将精灵帧合成为精灵表。

## 目录结构

```
sprite_sheet/
├── config.json              # 配置文件
├── input_frames/           # 输入精灵帧目录
│   ├── idle_down/         # 各动画子目录
│   │   ├── 001.png
│   │   ├── 002.png
│   │   └── ...
│   ├── walk_left/
│   │   ├── 001.png
│   │   └── ...
│   └── ...
├── output/                 # 输出精灵表
│   ├── spritesheet.png
│   ├── spritesheet.json
│   └── spritesheet.preview.png
└── README.md              # 本说明文件
```

## 如何使用

### 使用 MCP 工具

```python
# 基础合成
compose_sprite_sheet(
    project_dir="examples/sprite_sheet/character_sprite",
    generate_preview=True
)
```

### 直接使用工具类

```python
from src.comfyui_helper.sprite_composer import SpriteSheetComposer

# 加载配置并创建合成器
composer = SpriteSheetComposer()
config_path = "examples/sprite_sheet/character_sprite/config.json"
if Path(config_path).exists():
    config = composer.load_config_file(config_path)
    composer = SpriteSheetComposer(config)

# 合成精灵表
result = composer.create_sprite_sheet(
    input_dir="examples/sprite_sheet/character_sprite/input_frames",
    output_path="examples/sprite_sheet/character_sprite/output/spritesheet.png",
    generate_preview=True
)

print(f"成功合成精灵表，处理了 {result['processed_frames']} 帧")
```

## 配置说明

`config.json` 文件包含精灵表的配置：

```json
{
  "frame_width": 64,       // 单帧宽度
  "frame_height": 96,      // 单帧高度
  "cols": 8,              // 列数
  "rows": 16,             // 行数
  "background_color": [0, 0, 0, 0],  // 背景颜色 RGBA
  "animations": {         // 动画配置
    "idle_down": {"row": 0, "frames": 8},
    "walk_left": {"row": 1, "frames": 8}
    // ...
  }
}
```

## 精灵帧目录结构

精灵帧文件必须按照以下目录结构组织：
- 目录格式：`input_frames/{动画名称}/`
- 文件格式：`{帧序号}.png`（例如：001.png, 002.png）
- 完整路径示例：`input_frames/idle_down/001.png`

支持的动画类型（每个都是独立的子目录）：
- `idle_down`, `idle_left`, `idle_right`, `idle_up`
- `walk_down`, `walk_left`, `walk_right`, `walk_up`
- `run_down`, `run_left`, `run_right`, `run_up`
- `attack_down`, `attack_left`, `attack_right`, `attack_up`

## 输出文件

合成完成后会在 `output/` 目录生成：
- `*.png` - 精灵表图片
- `*.json` - Godot 引擎配置文件
- `*.preview.png` - 带网格预览图（如果启用）