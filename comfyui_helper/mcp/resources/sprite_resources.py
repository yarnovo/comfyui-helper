"""
精灵图相关的 MCP 资源
"""

from mcp.types import TextContent


def register_sprite_resources(mcp):
    """注册精灵图相关的 MCP 资源"""
    
    @mcp.resource("sprite://project-structure")
    def get_sprite_project_structure() -> str:
        """获取精灵图项目的标准目录结构说明"""
        return """# 精灵图项目结构

## 标准项目结构
```
project_name/
├── config.json          # 项目配置文件（必需）
├── input_frames/        # 输入帧目录（必需）
│   ├── frame_001.png
│   ├── frame_002.png
│   └── ...
└── output/             # 输出目录（自动创建）
    ├── spritesheet.png     # 生成的精灵表
    ├── spritesheet_preview.png # 预览图（可选）
    └── spritesheet_config.json # 输出配置
```

## 目录说明

### config.json
项目配置文件，定义精灵表的生成参数。

### input_frames/
存放所有要合并的精灵帧图片。支持 PNG、JPG、JPEG 格式。
- 建议使用连续编号命名（如 frame_001.png）
- 所有帧应具有相同尺寸

### output/
自动创建的输出目录，包含：
- 生成的精灵表图片
- 可选的预览图（带网格线）
- 配置信息文件

## 使用方法
1. 创建项目目录
2. 添加 config.json 配置文件
3. 将精灵帧放入 input_frames 目录
4. 运行 compose_sprite_sheet 工具"""

    @mcp.resource("sprite://config-template")
    def get_sprite_config_template() -> str:
        """获取精灵图配置文件模板"""
        return """{
    "name": "my_sprite_sheet",
    "frame_width": 64,
    "frame_height": 64,
    "columns": 8,
    "rows": null,
    "padding": 0,
    "background_color": [0, 0, 0, 0],
    "input_frames": "./input_frames",
    "optimize_size": true,
    "animation": {
        "fps": 12,
        "loop": true,
        "sequences": {
            "idle": [0, 1, 2, 3],
            "walk": [4, 5, 6, 7],
            "run": [8, 9, 10, 11],
            "jump": [12, 13, 14, 15]
        }
    },
    "metadata": {
        "author": "Your Name",
        "version": "1.0.0",
        "description": "精灵表描述"
    }
}"""

    @mcp.resource("sprite://example-project")
    def get_sprite_example_project() -> str:
        """获取精灵图项目示例"""
        return """# 精灵图项目示例

## 1. 角色动画精灵表
```json
{
    "name": "character_animations",
    "frame_width": 128,
    "frame_height": 128,
    "columns": 8,
    "padding": 2,
    "background_color": [0, 0, 0, 0],
    "animation": {
        "fps": 15,
        "sequences": {
            "idle": [0, 1, 2, 3],
            "walk": [4, 5, 6, 7, 8, 9, 10, 11],
            "attack": [12, 13, 14, 15, 16, 17]
        }
    }
}
```

## 2. UI图标精灵表
```json
{
    "name": "ui_icons",
    "frame_width": 32,
    "frame_height": 32,
    "columns": 16,
    "padding": 1,
    "background_color": [255, 255, 255, 0]
}
```

## 3. 粒子效果精灵表
```json
{
    "name": "particle_effects",
    "frame_width": 64,
    "frame_height": 64,
    "columns": 8,
    "optimize_size": true,
    "animation": {
        "fps": 30,
        "loop": false,
        "sequences": {
            "explosion": [0, 1, 2, 3, 4, 5, 6, 7],
            "smoke": [8, 9, 10, 11, 12, 13, 14, 15]
        }
    }
}
```"""