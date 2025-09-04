"""
精灵图相关的 MCP 资源
"""

from mcp.types import TextContent


def register_sprite_resources(mcp):
    """注册精灵图相关的 MCP 资源"""
    
    @mcp.resource("sprite://input-structure")
    def get_sprite_input_structure() -> str:
        """获取精灵图输入文件的标准目录结构说明"""
        return """# 精灵图输入文件结构

## 标准输入目录结构
```
input_folder/
├── idle/               # 待机动作序列
│   ├── frame_0000.png
│   ├── frame_0001.png
│   ├── frame_0002.png
│   └── ...
├── walk/               # 行走动作序列
│   ├── frame_0000.png
│   ├── frame_0001.png
│   ├── frame_0002.png
│   └── ...
├── run/                # 跑步动作序列
│   ├── frame_0000.png
│   ├── frame_0001.png
│   └── ...
└── attack/             # 攻击动作序列
    ├── frame_0000.png
    ├── frame_0001.png
    └── ...
```

## 目录说明

### 动作文件夹
- 每个子文件夹代表一个动作序列
- 文件夹名称即为动作名称（如 idle, walk, run, attack 等）
- 支持任意数量的动作文件夹

### 帧文件命名
- 使用统一格式：`frame_0000.png`, `frame_0001.png`, ...
- 序号必须连续，从 0000 开始
- 支持 PNG、JPG、JPEG 格式
- 同一动作内的所有帧应具有相同尺寸

## 输出结构
```
output_folder/
├── spritesheet.png    # 合成的精灵表图片
└── spritesheet.json   # 精灵表配置信息
```

## 配置文件内容
生成的 spritesheet.json 包含：
- frame_width/frame_height: 每帧的尺寸
- cols/rows: 精灵表的列数和行数
- animations: 每个动作的信息
  - row: 所在行号（从0开始）
  - frames: 帧数量

## 配置文件示例
```json
{
  "frame_width": 64,
  "frame_height": 96,
  "cols": 8,
  "rows": 2,
  "animations": {
    "idle": {
      "row": 0,
      "frames": 8
    },
    "walk": {
      "row": 1,
      "frames": 8
    }
  }
}
```

游戏引擎可以根据行号和帧数轻松计算：
- 起始坐标: x = 0, y = row * frame_height
- 每帧坐标: x = frame_index * frame_width, y = row * frame_height
- 动画播放: 从第0帧播放到第frames-1帧"""