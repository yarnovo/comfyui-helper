# 图片缩放示例

这个目录包含了图片缩放工具的测试示例。

## 文件说明

- `test_image.png` - 原始测试图片（512x1536 精灵表）
- `test_image_256x768.png` - 缩小一半的结果
- `test_128x128_aspect.png` - 指定尺寸并保持宽高比的结果
- `pixel_art_4x.png` - 像素艺术4倍放大（使用nearest算法）
- `batch_output/` - 批量缩放的输出目录

## 使用示例

### 1. 缩小图片一半
```python
scale_image(
    input_path="test_image.png",
    scale_factor=0.5
)
```

### 2. 缩放到指定尺寸（保持比例）
```python
scale_image(
    input_path="test_image.png",
    target_width=128,
    target_height=128,
    keep_aspect_ratio=True
)
```

### 3. 像素艺术放大
```python
scale_image(
    input_path="sprite.png",
    scale_factor=4,
    resampling="nearest"  # 保持锐利边缘
)
```

### 4. 批量处理
```python
batch_scale_images(
    input_dir="./input_frames",
    scale_factor=0.5,
    pattern="idle_*.png"
)
```

## 重采样算法对比

- **nearest**: 适合像素艺术，保持锐利边缘
- **lanczos**: 适合照片，平滑过渡（默认）
- **bilinear/bicubic**: 平衡选项

## 测试结果

所有测试均通过，工具可以：
- ✅ 按比例缩放
- ✅ 指定目标尺寸
- ✅ 保持宽高比
- ✅ 批量处理
- ✅ 不同重采样算法
- ✅ 自动生成输出文件名