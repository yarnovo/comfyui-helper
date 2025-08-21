# 脚本工具

本目录包含用于准备示例数据和辅助开发的脚本。

## 可用脚本

### generate_test_videos.py

为 examples/video_extraction 生成测试视频文件。

**功能：**
- 生成示例视频文件（如果不存在）
- 使用 ffmpeg 创建测试图案视频

**使用方法：**
```bash
python scripts/generate_test_videos.py
```

**生成的文件：**
```
examples/video_extraction/
└── sample_video.mp4        # 示例视频（5秒，320x240）
```

### generate_test_sprites.py

生成测试用的精灵帧图片，用于精灵图合成功能测试。

**功能：**
- 创建不同动画类型的精灵帧
- 支持多个方向（上下左右）
- 生成带标签的测试图片

**使用方法：**
```bash
python scripts/generate_test_sprites.py
```

**生成的文件：**
```
character_sprite/input_frames/
├── idle_down_001.png       # 待机动画帧
├── walk_left_001.png       # 行走动画帧
└── ...
```

## 脚本开发指南

### 添加新脚本

1. 在 `scripts/` 目录创建新的 Python 文件
2. 添加适当的文档字符串
3. 使用绝对导入路径
4. 添加 `if __name__ == "__main__":` 保护

### 脚本模板

```python
#!/usr/bin/env python3
"""
脚本描述
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def main():
    """主函数"""
    pass

if __name__ == "__main__":
    main()
```

## 常用功能

### 生成测试视频

```python
def create_test_video(output_path, duration=10, fps=30):
    """使用 ffmpeg 创建测试视频"""
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"testsrc=duration={duration}:size=640x480:rate={fps}",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        str(output_path)
    ]
    subprocess.run(cmd, check=True)
```

### 批量处理文件

```python
def process_files(input_dir, output_dir, pattern="*.png"):
    """批量处理文件"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    for file in input_path.glob(pattern):
        # 处理文件
        pass
```

## 依赖要求

- Python 3.8+
- ffmpeg（用于视频处理）
- Pillow（用于图像处理）

## 注意事项

1. 脚本应该是独立可运行的
2. 使用清晰的命名和文档
3. 处理错误情况
4. 提供有用的输出信息