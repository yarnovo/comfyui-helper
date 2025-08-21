# 使用示例

本目录包含 ComfyUI Helper 工具的实际使用示例项目。

## 目录结构

```
examples/
├── sprite_sheet/         # 精灵图合成示例项目
│   ├── character_sprite/ # 示例精灵图项目
│   └── README.md        # 精灵图合成使用说明
└── video_extraction/    # 视频帧提取示例项目
    ├── sample_video.mp4 # 示例视频文件
    ├── output_frames/   # 帧提取输出目录
    └── README.md       # 视频帧提取使用说明
```

## 快速开始

### 1. 精灵图合成示例

```bash
# 使用 MCP 工具合成精灵表
compose_sprite_sheet(
    project_dir="examples/sprite_sheet/character_sprite",
    generate_preview=True
)
```

参考 `examples/sprite_sheet/README.md` 了解详细使用说明。

### 2. 视频帧提取示例

```bash
# 使用 MCP 工具提取视频帧
extract_video_frames(
    video_url="examples/video_extraction/sample_video.mp4",
    output_dir="examples/video_extraction/output_frames",
    fps=1
)
```

参考 `examples/video_extraction/README.md` 了解详细使用说明。

## 工具说明

### 精灵图合成工具 (sprite_composer.py)

将多个精灵帧图片合成为精灵表，支持：
- 自定义帧尺寸和排列
- 多种动画类型和方向
- Godot 引擎配置文件生成
- 预览图生成

### 视频帧提取工具 (video_frame_extractor.py)

从视频中提取帧图片，支持：
- 按帧率提取
- 按总帧数提取
- 按时间间隔提取
- 提取关键帧
- 指定时间范围
- 多种输出格式

## 更多信息

- 查看各示例项目的 README.md 了解详细使用方法
- 运行 `tests/` 中的测试代码验证功能
- 查看 [开发文档](../DEVELOPMENT.md) 了解工具实现