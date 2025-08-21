#!/usr/bin/env python3
"""
ComfyUI Helper MCP Server 主入口
使用 FastMCP 简化实现
"""

import json
import logging
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from mcp.types import Resource, TextContent

from .sprite_composer import SpriteSheetComposer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建 FastMCP 服务器
mcp = FastMCP("comfyui-helper")


@mcp.tool()
def compose_sprite_sheet(project_dir: str, generate_preview: bool = True) -> str:
    """
    处理精灵图项目文件夹，将input_frames中的精灵帧拼接成精灵表并输出到output目录
    
    Args:
        project_dir: 项目文件夹路径，包含config.json配置文件和input_frames输入帧目录
        generate_preview: 是否生成带网格线的预览图
        
    Returns:
        处理结果信息
    """
    try:
        project_path = Path(project_dir)
        
        # 验证项目结构
        if not project_path.exists():
            return f"❌ 项目目录不存在: {project_dir}"
        
        config_file = project_path / "config.json"
        input_frames_dir = project_path / "input_frames"
        output_dir = project_path / "output"
        
        # 检查必要文件和目录
        if not input_frames_dir.exists():
            return f"❌ 未找到输入帧目录: {input_frames_dir}"
        
        # 创建输出目录
        output_dir.mkdir(exist_ok=True)
        
        # 加载配置
        composer = SpriteSheetComposer()
        if config_file.exists():
            config = composer.load_config_file(str(config_file))
            composer = SpriteSheetComposer(config)
            logger.info(f"已加载配置文件: {config_file}")
        else:
            logger.info("使用默认配置")
        
        # 生成输出文件名
        project_name = project_path.name
        output_path = output_dir / f"{project_name}_spritesheet.png"
        
        # 创建精灵表
        result = composer.create_sprite_sheet(
            str(input_frames_dir),
            str(output_path),
            generate_preview
        )
        
        if result["success"]:
            response_text = f"""✅ {result['message']}

项目: {project_name}
输入目录: {input_frames_dir}

输出文件:
- 精灵表: {result['output_path']}
- 配置文件: {result['config_path']}"""
            
            if result.get('preview_path'):
                response_text += f"\n- 预览图: {result['preview_path']}"
            
            response_text += f"""

精灵表信息:
- 尺寸: {result['sheet_width']}x{result['sheet_height']}
- 已处理帧数: {result['processed_frames']}
- 缺失帧数: {result['missing_frames']}"""
        else:
            response_text = f"❌ {result['message']}"
        
        return response_text
        
    except Exception as e:
        return f"❌ 错误: {str(e)}"


# 资源定义
@mcp.resource("sprite://project-structure")
def get_project_structure() -> str:
    """获取精灵图项目的标准目录结构说明"""
    return """# 精灵图项目目录结构

## 必需的目录结构
```
your_project/              # 项目根目录
├── config.json           # 配置文件（可选，不存在则使用默认配置）
├── input_frames/         # 输入精灵帧目录（必需）
│   ├── idle_down_001.png
│   ├── idle_down_002.png
│   ├── walk_left_01.png
│   └── ...
└── output/              # 输出目录（自动创建）
    ├── xxx_spritesheet.png      # 生成的精灵表
    ├── xxx_spritesheet.json     # Godot 配置文件
    └── xxx_spritesheet.preview.png # 预览图（可选）
```

## 文件命名规范
精灵帧文件必须按照以下格式命名：
- 格式：`{动画名}_{方向}_{帧序号}.png`
- 示例：`idle_down_001.png`, `walk_left_01.png`, `attack_up_1.png`
- 帧序号可以是 1, 01, 001 等格式

## 支持的动画类型
- idle_down, idle_left, idle_right, idle_up
- walk_down, walk_left, walk_right, walk_up
- run_down, run_left, run_right, run_up
- attack_down, attack_left, attack_right, attack_up
"""


@mcp.resource("sprite://config-template")
def get_config_template() -> str:
    """获取 config.json 配置文件模板"""
    config = {
        "frame_width": 64,
        "frame_height": 96,
        "cols": 8,
        "rows": 16,
        "background_color": [0, 0, 0, 0],
        "animations": {
            "idle_down": {"row": 0, "frames": 8},
            "idle_left": {"row": 1, "frames": 8},
            "idle_right": {"row": 2, "frames": 8},
            "idle_up": {"row": 3, "frames": 8},
            "walk_down": {"row": 4, "frames": 8},
            "walk_left": {"row": 5, "frames": 8},
            "walk_right": {"row": 6, "frames": 8},
            "walk_up": {"row": 7, "frames": 8},
            "run_down": {"row": 8, "frames": 6},
            "run_left": {"row": 9, "frames": 6},
            "run_right": {"row": 10, "frames": 6},
            "run_up": {"row": 11, "frames": 6},
            "attack_down": {"row": 12, "frames": 4},
            "attack_left": {"row": 13, "frames": 4},
            "attack_right": {"row": 14, "frames": 4},
            "attack_up": {"row": 15, "frames": 4}
        }
    }
    
    return f"""# config.json 配置文件模板

将以下 JSON 保存为 `config.json` 放在项目根目录：

```json
{json.dumps(config, indent=2, ensure_ascii=False)}
```

## 配置说明

- **frame_width**: 单个精灵帧的宽度（像素）
- **frame_height**: 单个精灵帧的高度（像素）
- **cols**: 精灵表的列数
- **rows**: 精灵表的行数
- **background_color**: 背景颜色 [R, G, B, A]，范围 0-255
- **animations**: 动画配置
  - **row**: 该动画在精灵表中的行号（从0开始）
  - **frames**: 该动画的帧数

## 注意事项

1. 每个动画占据一行
2. 如果实际帧数少于配置的 frames，会留空
3. 如果实际帧数多于配置的 frames，多余的会被忽略
4. 可以根据需要调整每个动画的帧数
"""


@mcp.resource("sprite://example-project") 
def get_example_project() -> str:
    """获取示例项目的创建步骤"""
    return """# 创建示例精灵图项目

## 步骤 1：创建项目目录
```bash
mkdir my_character
cd my_character
mkdir input_frames
```

## 步骤 2：准备精灵帧图片
将您的精灵帧图片放入 `input_frames/` 目录，命名示例：
```
input_frames/
├── idle_down_001.png
├── idle_down_002.png
├── idle_down_003.png
├── idle_down_004.png
├── walk_left_001.png
├── walk_left_002.png
├── walk_left_003.png
└── ...
```

## 步骤 3：（可选）创建配置文件
如果需要自定义配置，创建 `config.json`：
```json
{
  "frame_width": 64,
  "frame_height": 96,
  "cols": 8,
  "rows": 16,
  "background_color": [0, 0, 0, 0]
}
```

## 步骤 4：使用工具生成精灵表
在 Claude 中运行：
```
compose_sprite_sheet(
  project_dir="/path/to/my_character",
  generate_preview=true
)
```

## 输出结果
工具会在 `output/` 目录生成：
- `my_character_spritesheet.png` - 精灵表图片
- `my_character_spritesheet.json` - Godot 配置文件
- `my_character_spritesheet.preview.png` - 带网格的预览图（如果启用）

## 提示
- 确保所有帧图片尺寸一致
- 使用透明背景的 PNG 格式
- 按照命名规范组织文件
"""


# 未来可以继续添加工具
# @mcp.tool()
# def another_tool(param1: str) -> str:
#     """另一个工具的描述"""
#     return f"处理: {param1}"


if __name__ == "__main__":
    logger.info("ComfyUI Helper MCP Server 已启动 (FastMCP)")
    mcp.run()