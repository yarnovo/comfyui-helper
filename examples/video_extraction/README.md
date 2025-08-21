# 视频帧提取示例

这个示例演示如何使用视频帧提取工具从视频中提取帧。

## 目录结构

```
video_extraction/
├── sample_video.mp4      # 示例视频文件
├── output_frames/        # 帧提取输出目录
└── README.md            # 本说明文件
```

## 如何使用

### 使用 MCP 工具

```python
# 基础提取 - 每秒1帧
extract_video_frames(
    video_url="examples/video_extraction/sample_video.mp4",
    output_dir="examples/video_extraction/output_frames/basic",
    fps=1
)

# 按总帧数提取 - 提取10帧
extract_video_frames(
    video_url="examples/video_extraction/sample_video.mp4",
    output_dir="examples/video_extraction/output_frames/count",
    frame_count=10
)

# 按时间间隔提取 - 每0.5秒一帧
extract_video_frames(
    video_url="examples/video_extraction/sample_video.mp4",
    output_dir="examples/video_extraction/output_frames/interval",
    interval=0.5
)

# 提取关键帧
extract_video_frames(
    video_url="examples/video_extraction/sample_video.mp4",
    output_dir="examples/video_extraction/output_frames/keyframes",
    extract_keyframes=True
)
```

### 直接使用工具类

```python
from src.comfyui_helper.video_frame_extractor import VideoFrameExtractor

extractor = VideoFrameExtractor()

# 提取帧
result = extractor.extract_frames(
    video_path="examples/video_extraction/sample_video.mp4",
    output_dir="examples/video_extraction/output_frames/direct",
    fps=2
)

print(f"提取了 {result['frame_count']} 帧")
```

## 输出说明

提取的帧图片将保存在 `output_frames/` 目录的相应子目录中：
- `frame_000001.png`, `frame_000002.png` 等

每个子目录对应不同的提取方式：
- `basic/` - 基础按帧率提取
- `count/` - 按总帧数提取
- `interval/` - 按时间间隔提取
- `keyframes/` - 关键帧提取
- `direct/` - 直接使用工具类