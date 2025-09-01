"""
使用指南相关的 MCP 资源
"""

from mcp.types import TextContent


def register_guide_resources(mcp):
    """注册使用指南相关的 MCP 资源"""
    
    @mcp.resource("video://extraction-guide")
    def get_video_extraction_guide() -> str:
        """获取视频帧提取使用指南"""
        return """# 🎬 视频帧提取工具使用指南

## 功能特点
- 支持多种视频格式（MP4, AVI, MOV, MKV, WEBM 等）
- 灵活的帧提取模式（固定帧率、固定间隔、固定数量）
- 支持关键帧提取
- 自定义输出格式和质量

## 提取模式

### 1. 固定帧率提取 (fps)
每秒提取指定数量的帧
```python
extract_video_frames(
    video_url="video.mp4",
    output_dir="./frames",
    fps=2  # 每秒提取2帧
)
```

### 2. 固定间隔提取 (interval)
每隔指定秒数提取一帧
```python
extract_video_frames(
    video_url="video.mp4",
    output_dir="./frames",
    interval=5  # 每5秒提取一帧
)
```

### 3. 固定数量提取 (frame_count)
从视频中均匀提取指定数量的帧
```python
extract_video_frames(
    video_url="video.mp4",
    output_dir="./frames",
    frame_count=10  # 总共提取10帧
)
```

### 4. 关键帧提取 (extract_keyframes)
只提取视频的关键帧（I帧）
```python
extract_video_frames(
    video_url="video.mp4",
    output_dir="./frames",
    extract_keyframes=True
)
```

## 高级选项

### 时间范围控制
```python
extract_video_frames(
    video_url="video.mp4",
    output_dir="./frames",
    start_time=10,    # 从第10秒开始
    duration=30,      # 持续30秒
    fps=1            # 每秒1帧
)
```

### 输出格式设置
```python
extract_video_frames(
    video_url="video.mp4",
    output_dir="./frames",
    output_format="jpg",   # 输出为JPEG
    quality=5,            # JPEG质量 (1-31, 1最高)
    output_prefix="frame"  # 文件前缀
)
```

## 使用建议

1. **游戏动画提取**：使用固定帧率（fps）模式
2. **视频预览生成**：使用固定数量（frame_count）模式
3. **场景变化检测**：使用关键帧（extract_keyframes）模式
4. **定时截图**：使用固定间隔（interval）模式

## 注意事项
- 输出文件名格式：`{prefix}_{number}.{format}`
- 编号自动补零，确保正确排序
- 大视频文件建议使用 start_time 和 duration 限制范围"""

    @mcp.resource("background://removal-guide")
    def get_background_removal_guide() -> str:
        """获取背景移除使用指南"""
        return """# 🎨 RMBG-2.0 背景移除工具使用指南

## 功能特点
- 使用先进的 RMBG-2.0 AI 模型
- 支持透明背景和白色背景
- 高质量边缘检测
- GPU 加速支持（自动检测）
- 批量处理功能

## 单张图像处理

### 基础用法
```python
remove_background(
    input_path="/path/to/image.png"
)
```

### 完整参数
```python
remove_background(
    input_path="/path/to/image.png",
    output_path="/path/to/output.png",
    use_white_bg=False,  # False=透明背景, True=白色背景
    alpha_threshold=0     # Alpha阈值 (0-255)
)
```

## 批量处理

### 处理整个目录
```python
batch_remove_background(
    input_dir="/path/to/images",
    output_dir="/path/to/output",
    use_white_bg=False,
    alpha_threshold=0,
    extensions=['.png', '.jpg', '.jpeg', '.webp']
)
```

## 参数说明

### use_white_bg
- `False`（默认）：生成透明背景（PNG格式）
- `True`：生成白色背景

### alpha_threshold
- 范围：0-255
- 作用：低于此值的像素将完全透明
- 0（默认）：保留所有半透明像素
- 128：将半透明像素二值化

## 使用场景

### 1. 产品图片处理
```python
remove_background(
    input_path="product.jpg",
    use_white_bg=True  # 电商平台通常需要白底
)
```

### 2. 人像抠图
```python
remove_background(
    input_path="portrait.jpg",
    use_white_bg=False,  # 透明背景便于合成
    alpha_threshold=10   # 轻微的阈值处理
)
```

### 3. 批量处理素材
```python
batch_remove_background(
    input_dir="./raw_images",
    output_dir="./processed",
    extensions=['.png', '.jpg']
)
```

## 性能优化

1. **GPU 加速**：自动检测并使用 CUDA（如果可用）
2. **批量处理**：使用 batch_remove_background 提高效率
3. **模型缓存**：首次加载后模型会缓存，后续处理更快

## 输出格式

- 透明背景：RGBA PNG 格式
- 白色背景：RGB PNG 格式
- 保持原始图像尺寸
- 高质量边缘处理

## 注意事项

- 首次运行需要下载模型（约 176MB）
- 建议图像尺寸不超过 4096x4096
- 支持格式：PNG, JPG, JPEG, WEBP
- 输出文件默认添加 `_no_bg` 后缀"""