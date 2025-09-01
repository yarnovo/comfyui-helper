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

from .tools.sprite_composer import SpriteSheetComposer
from .tools.video_frame_extractor import VideoFrameExtractor
from .tools.image_scaler import ImageScaler
from .tools.background_remover import BackgroundRemover

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
        output_dir = project_path / "output"
        
        # 创建输出目录
        output_dir.mkdir(exist_ok=True)
        
        # 加载配置 - 配置文件必须存在
        if not config_file.exists():
            return f"❌ 配置文件不存在: {config_file}\n请创建 config.json 文件，包含必要的配置字段"
        
        try:
            config = SpriteSheetComposer.load_config_file(str(config_file))
            composer = SpriteSheetComposer(config)
            logger.info(f"已加载配置文件: {config_file}")
        except FileNotFoundError as e:
            return f"❌ {str(e)}"
        except json.JSONDecodeError as e:
            return f"❌ 配置文件格式错误: {str(e)}"
        except ValueError as e:
            return f"❌ 配置文件验证失败: {str(e)}"
        except Exception as e:
            return f"❌ 加载配置文件失败: {str(e)}"
        
        # 从配置中获取 input_frames 路径，如果没有则使用默认值
        input_frames_path = config.get('input_frames', './input_frames')
        
        # 处理相对路径和绝对路径
        if Path(input_frames_path).is_absolute():
            # 绝对路径直接使用
            input_frames_dir = Path(input_frames_path)
        else:
            # 相对路径相对于项目目录
            input_frames_dir = project_path / input_frames_path
        
        # 检查输入帧目录是否存在
        if not input_frames_dir.exists():
            return f"❌ 未找到输入帧目录: {input_frames_dir}"
        
        # 使用固定的输出文件名
        output_path = output_dir / "spritesheet.png"
        
        # 创建精灵表
        result = composer.create_sprite_sheet(
            str(input_frames_dir),
            str(output_path),
            generate_preview
        )
        
        if result["success"]:
            response_text = f"""✅ {result['message']}

项目: {project_path.name}
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
├── config.json           # 配置文件（必需）
├── input_frames/         # 输入精灵帧目录（必需）
│   ├── idle_down/       # 动画子目录
│   │   ├── 001.png
│   │   ├── 002.png
│   │   └── ...
│   ├── walk_left/       # 动画子目录
│   │   ├── 001.png
│   │   └── ...
│   └── ...
└── output/              # 输出目录（自动创建）
    ├── spritesheet.png      # 生成的精灵表
    ├── spritesheet.json     # 精灵表描述文件
    └── spritesheet.preview.png # 预览图（可选）
```

## 文件组织规范
精灵帧文件必须按照以下方式组织：
- 目录结构：`input_frames/{动画名称}/{帧序号}.png`
- 示例：`input_frames/idle_down/001.png`, `input_frames/walk_left/001.png`
- 帧序号建议使用3位数字格式（001, 002, 003...）

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

### 必需字段
- **frame_width**: 单个精灵帧的宽度（像素）
- **frame_height**: 单个精灵帧的高度（像素）
- **cols**: 精灵表的列数
- **rows**: 精灵表的行数
- **animations**: 动画配置对象（必需，决定输出布局）

### 可选字段
- **input_frames**: 输入帧目录路径（默认 "./input_frames"）
  - 支持相对路径：相对于项目目录，如 "./frames"、"../sprites"
  - 支持绝对路径：如 "/home/user/sprites"
- **background_color**: 背景颜色 [R, G, B, A]，范围 0-255，默认 [0, 0, 0, 0]（透明）

### animations 配置详解
`animations` 是核心配置，直接决定输出精灵表的结构：
- 每个键是动画名称（如 `idle_down`、`walk_left`）
- `row`: 该动画在精灵表中的行号（从0开始）
- `frames`: 该动画占用的帧数（列数）

**工作原理**：
1. 程序扫描 input_frames 目录中的文件
2. 根据子目录名称（如 `idle_down/001.png` → `idle_down`）匹配动画配置
3. 将匹配到的帧按序号排列在指定行
4. 未在 animations 中定义的动画文件将被忽略

## 注意事项

1. animations 配置是必需的，它定义了输出精灵表的完整布局
2. 只有在 animations 中定义的动画才会被处理
3. 如果实际帧数少于配置的 frames，会在该行留出空白格子
4. 如果实际帧数多于配置的 frames，多余的帧会被忽略
5. 输出图片尺寸 = (cols × frame_width) × (rows × frame_height)
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
将您的精灵帧图片按动画类型组织到子目录中：
```
input_frames/
├── idle_down/
│   ├── 001.png
│   ├── 002.png
│   ├── 003.png
│   └── 004.png
├── walk_left/
│   ├── 001.png
│   ├── 002.png
│   └── 003.png
└── ...
```

## 步骤 3：创建配置文件（必需）
创建 `config.json` 文件：
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
- `spritesheet.png` - 精灵表图片
- `spritesheet.json` - 精灵表描述文件（包含帧位置、尺寸等信息）
- `spritesheet.preview.png` - 带网格的预览图（如果启用）

## 提示
- 确保所有帧图片尺寸一致
- 使用透明背景的 PNG 格式
- 按照命名规范组织文件
"""


@mcp.tool()
def extract_video_frames(
    video_url: str,
    output_dir: str,
    fps: float = None,
    start_time: float = None,
    duration: float = None,
    frame_count: int = None,
    interval: float = None,
    extract_keyframes: bool = False,
    output_format: str = "png",
    output_prefix: str = "frame",
    quality: int = 2
) -> str:
    """
    从视频中提取帧图片
    
    Args:
        video_url: 视频文件路径或URL
        output_dir: 输出目录路径
        fps: 提取帧率（每秒提取多少帧），与 frame_count/interval 互斥
        start_time: 开始时间（秒）
        duration: 持续时间（秒）
        frame_count: 要提取的总帧数，与 fps/interval 互斥
        interval: 时间间隔（秒），每隔多少秒提取一帧，与 fps/frame_count 互斥
        extract_keyframes: 是否只提取关键帧（I帧）
        output_format: 输出图片格式（png, jpg, jpeg）
        output_prefix: 输出文件前缀
        quality: JPEG 质量（1-31，1 最高质量，仅对 jpg/jpeg 有效）
    
    Returns:
        处理结果信息
    """
    try:
        extractor = VideoFrameExtractor()
        
        # 参数验证
        param_count = sum([fps is not None, frame_count is not None, interval is not None])
        if param_count > 1:
            return "❌ 错误：fps、frame_count 和 interval 参数只能指定其中一个"
        
        # 根据不同模式调用相应方法
        if extract_keyframes:
            result = extractor.extract_keyframes(
                video_path=video_url,
                output_dir=output_dir,
                output_format=output_format,
                output_prefix="keyframe",
                quality=quality
            )
        elif interval is not None:
            result = extractor.extract_frames_by_interval(
                video_path=video_url,
                output_dir=output_dir,
                interval=interval,
                output_format=output_format,
                output_prefix=output_prefix,
                quality=quality
            )
        else:
            result = extractor.extract_frames(
                video_path=video_url,
                output_dir=output_dir,
                fps=fps,
                start_time=start_time,
                duration=duration,
                frame_count=frame_count,
                output_format=output_format,
                output_prefix=output_prefix,
                quality=quality
            )
        
        if result["success"]:
            response_text = f"""✅ {result['message']}

视频信息:
- 时长: {result.get('video_info', {}).get('duration', 0):.2f} 秒
- 帧率: {result.get('video_info', {}).get('fps', 0):.2f} fps
- 分辨率: {result.get('video_info', {}).get('width', 0)}x{result.get('video_info', {}).get('height', 0)}
- 编码: {result.get('video_info', {}).get('codec', 'unknown')}

输出信息:
- 输出目录: {result['output_dir']}
- 提取帧数: {result['frame_count']}
- 图片格式: {output_format}"""
            
            # 显示前几个文件名
            if result.get('files'):
                files_to_show = result['files'][:5]
                response_text += f"\n\n已生成文件（显示前{min(5, len(result['files']))}个）:"
                for file in files_to_show:
                    response_text += f"\n- {Path(file).name}"
                if len(result['files']) > 5:
                    response_text += f"\n... 还有 {len(result['files']) - 5} 个文件"
        else:
            response_text = f"❌ {result['message']}"
        
        return response_text
        
    except Exception as e:
        return f"❌ 错误: {str(e)}"


@mcp.resource("video://extraction-guide")
def get_video_extraction_guide() -> str:
    """获取视频帧提取使用指南"""
    return """# 视频帧提取工具使用指南

## 功能概述
从视频文件中提取指定的帧作为图片，支持多种提取模式。

## 提取模式

### 1. 按帧率提取
```python
extract_video_frames(
    video_url="video.mp4",
    output_dir="./frames",
    fps=1  # 每秒提取1帧
)
```

### 2. 按帧数提取
```python
extract_video_frames(
    video_url="video.mp4", 
    output_dir="./frames",
    frame_count=30  # 总共提取30帧，均匀分布
)
```

### 3. 按时间间隔提取
```python
extract_video_frames(
    video_url="video.mp4",
    output_dir="./frames",
    interval=2.5  # 每2.5秒提取一帧
)
```

### 4. 提取关键帧
```python
extract_video_frames(
    video_url="video.mp4",
    output_dir="./frames",
    extract_keyframes=True  # 只提取I帧（关键帧）
)
```

### 5. 指定时间范围
```python
extract_video_frames(
    video_url="video.mp4",
    output_dir="./frames",
    start_time=10,  # 从第10秒开始
    duration=30,    # 持续30秒
    fps=2          # 每秒提取2帧
)
```

## 参数说明

- **video_url**: 视频文件路径
- **output_dir**: 输出目录路径（自动创建）
- **fps**: 提取帧率（帧/秒）
- **frame_count**: 总帧数（均匀分布）
- **interval**: 时间间隔（秒）
- **start_time**: 开始时间（秒）
- **duration**: 持续时间（秒）
- **extract_keyframes**: 是否只提取关键帧
- **output_format**: 输出格式（png/jpg/jpeg）
- **output_prefix**: 文件名前缀
- **quality**: JPEG质量（1-31，1最高）

## 注意事项

1. fps、frame_count、interval 三个参数互斥，只能指定一个
2. 需要系统安装 ffmpeg
3. 输出文件命名格式：{prefix}_{序号}.{format}
4. PNG 格式无损，JPG 格式有损但文件更小
"""


@mcp.tool()
def scale_image(
    input_path: str,
    output_path: str = None,
    scale_factor: float = None,
    target_width: int = None,
    target_height: int = None,
    keep_aspect_ratio: bool = True,
    resampling: str = 'lanczos',
    quality: int = 95
) -> str:
    """
    缩放单张图片
    
    Args:
        input_path: 输入图片路径
        output_path: 输出图片路径（可选，默认在同目录生成 {原名}_{宽}x{高}.{扩展名}）
        scale_factor: 缩放倍数（如0.5=缩小一半，2=放大一倍）
        target_width: 目标宽度（像素）
        target_height: 目标高度（像素）
        keep_aspect_ratio: 是否保持宽高比
        resampling: 重采样算法（nearest适合像素艺术/bilinear/bicubic/lanczos适合照片）
        quality: JPEG质量（1-100，仅对JPEG有效）
        
    Returns:
        处理结果信息
    """
    try:
        scaler = ImageScaler()
        
        # 验证参数
        if not any([scale_factor, target_width, target_height]):
            return "❌ 错误：必须指定 scale_factor、target_width 或 target_height 至少一个参数"
        
        result = scaler.scale_image(
            input_path=input_path,
            output_path=output_path,
            scale_factor=scale_factor,
            target_width=target_width,
            target_height=target_height,
            keep_aspect_ratio=keep_aspect_ratio,
            resampling=resampling,
            quality=quality
        )
        
        if result["success"]:
            response_text = f"""✅ {result['message']}

图片信息:
- 原始尺寸: {result['original_size'][0]}x{result['original_size'][1]}
- 新尺寸: {result['new_size'][0]}x{result['new_size'][1]}
- 缩放比例: {result['scale_factor']:.2f}x
- 输出文件: {result['output_path']}"""
        else:
            response_text = f"❌ {result['message']}"
        
        return response_text
        
    except Exception as e:
        return f"❌ 错误: {str(e)}"


@mcp.tool()
def remove_background(
    input_path: str,
    output_path: str = None,
    use_white_bg: bool = False,
    alpha_threshold: int = 0
) -> str:
    """
    使用 RMBG-2.0 模型移除图像背景
    
    Args:
        input_path: 输入图像路径
        output_path: 输出路径（可选，默认在同目录生成 {原名}_no_bg.png）
        use_white_bg: 是否使用白色背景（False=透明背景，True=白色背景）
        alpha_threshold: Alpha 阈值（0-255），低于此值的像素将完全透明
        
    Returns:
        处理结果信息
    """
    try:
        from pathlib import Path
        
        # 创建背景移除器（自动选择最佳设备）
        remover = BackgroundRemover()
        
        # 处理输入路径
        input_file = Path(input_path)
        if not input_file.exists():
            return f"❌ 错误：输入文件不存在: {input_path}"
        
        # 设置输出路径
        if output_path is None:
            output_path = input_file.parent / f"{input_file.stem}_no_bg.png"
        else:
            output_path = Path(output_path)
            
        # 移除背景
        result_image = remover.remove_background(
            image=input_file,
            output_path=output_path,
            alpha_matting=not use_white_bg,
            alpha_threshold=alpha_threshold
        )
        
        # 清理缓存
        remover.clear_cache()
        
        response_text = f"""✅ 背景移除成功！

图像信息:
- 输入文件: {input_path}
- 输出文件: {output_path}
- 背景类型: {'白色背景' if use_white_bg else '透明背景'}
- Alpha 阈值: {alpha_threshold}
- 使用设备: {remover.device.upper()}
- 图像尺寸: {result_image.size[0]}x{result_image.size[1]}"""
        
        return response_text
        
    except Exception as e:
        logger.error(f"背景移除失败: {e}")
        return f"❌ 错误: {str(e)}"


@mcp.tool()
def batch_remove_background(
    input_dir: str,
    output_dir: str = None,
    use_white_bg: bool = False,
    alpha_threshold: int = 0,
    extensions: list = None
) -> str:
    """
    批量移除多个图像的背景
    
    Args:
        input_dir: 输入目录路径
        output_dir: 输出目录路径（可选，默认在输入目录创建 {目录名}_no_bg/）
        use_white_bg: 是否使用白色背景（False=透明背景，True=白色背景）
        alpha_threshold: Alpha 阈值（0-255），低于此值的像素将完全透明
        extensions: 支持的文件扩展名列表（默认: ['.png', '.jpg', '.jpeg', '.webp']）
        
    Returns:
        处理结果信息
    """
    try:
        from pathlib import Path
        
        # 创建背景移除器（自动选择最佳设备）
        remover = BackgroundRemover()
        
        # 处理路径
        input_path = Path(input_dir)
        if not input_path.exists() or not input_path.is_dir():
            return f"❌ 错误：输入目录不存在或不是目录: {input_dir}"
        
        # 设置输出目录
        if output_dir is None:
            output_path = input_path.parent / f"{input_path.name}_no_bg"
        else:
            output_path = Path(output_dir)
            
        # 设置扩展名
        if extensions is None:
            extensions = ['.png', '.jpg', '.jpeg', '.webp']
        
        # 批量处理
        processed = remover.batch_remove_background(
            input_dir=input_path,
            output_dir=output_path,
            extensions=tuple(extensions),
            alpha_matting=not use_white_bg,
            alpha_threshold=alpha_threshold
        )
        
        # 清理缓存
        remover.clear_cache()
        
        response_text = f"""✅ 批量背景移除完成！

处理信息:
- 输入目录: {input_dir}
- 输出目录: {output_path}
- 处理文件数: {processed}
- 背景类型: {'白色背景' if use_white_bg else '透明背景'}
- Alpha 阈值: {alpha_threshold}
- 使用设备: {remover.device.upper()}
- 支持格式: {', '.join(extensions)}"""
        
        return response_text
        
    except Exception as e:
        logger.error(f"批量背景移除失败: {e}")
        return f"❌ 错误: {str(e)}"


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
    use_white_bg=False,      # False=透明背景，True=白色背景
    alpha_threshold=0         # 0-255，边缘清晰度控制
)
```

## 批量处理

### 处理整个目录
```python
batch_remove_background(
    input_dir="/path/to/images/",
    output_dir="/path/to/output/",
    use_white_bg=False,
    alpha_threshold=0,
    extensions=['.png', '.jpg', '.jpeg']
)
```

## 参数说明

### 背景类型
- **透明背景**（默认）：适合需要合成的场景
- **白色背景**：适合不支持透明度的场景

### Alpha 阈值
- **0**（默认）：保留所有半透明像素，边缘更柔和
- **50-100**：中等阈值，平衡边缘质量
- **150-255**：高阈值，边缘更锐利但可能丢失细节

### 设备选择
系统会自动检测并选择最佳设备：
- 优先使用 GPU（CUDA）以获得最佳性能
- 如果 GPU 不可用，自动降级到 CPU

## 使用场景

### 1. 产品图片处理
```python
remove_background(
    input_path="product.jpg",
    use_white_bg=True,      # 电商常用白底
    alpha_threshold=100     # 清晰边缘
)
```

### 2. 人像抠图
```python
remove_background(
    input_path="portrait.jpg",
    use_white_bg=False,     # 透明背景便于合成
    alpha_threshold=0       # 保留头发细节
)
```

### 3. 批量处理游戏素材
```python
batch_remove_background(
    input_dir="sprites/",
    use_white_bg=False,     # 游戏素材需要透明背景
    extensions=['.png']     # 只处理 PNG 文件
)
```

## 性能提示

1. **GPU 加速**：RTX 显卡处理速度比 CPU 快 5-10 倍
2. **批量处理**：使用批量功能比逐个处理更高效
3. **图像尺寸**：建议不超过 4K 分辨率以获得最佳效果
4. **内存使用**：首次运行会下载约 176MB 的模型文件

## 注意事项

- 首次运行需要下载模型（自动完成）
- 模型缓存在 `~/.cache/comfyui-helper/models/`
- 支持格式：PNG、JPG、JPEG、WebP
- 输出默认为 PNG 格式（支持透明度）
"""

if __name__ == "__main__":
    logger.info("ComfyUI Helper MCP Server 已启动 (FastMCP)")
    mcp.run()