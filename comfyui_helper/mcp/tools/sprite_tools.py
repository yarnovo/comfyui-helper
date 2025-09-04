"""
精灵图相关的 MCP 工具
"""

import json
import logging
from pathlib import Path
from typing import Optional
from ...core.sprite_composer import SpriteSheetComposer

logger = logging.getLogger(__name__)


def register_sprite_tools(mcp):
    """注册精灵图相关的 MCP 工具"""
    
    @mcp.tool()
    def compose_sprite_sheet(
        input_dir: str,
        output_dir: str,
        background_color: Optional[list] = None
    ) -> str:
        """
        处理包含多个动作序列的精灵图文件夹，每个子文件夹代表一个动作
        
        Args:
            input_dir: 输入文件夹路径，包含多个动作子文件夹
            output_dir: 输出文件夹路径
            background_color: 背景颜色 [R, G, B, A]（默认透明）
            
        Returns:
            处理结果信息
        """
        try:
            input_path = Path(input_dir)
            output_path = Path(output_dir)
            
            # 验证输入目录
            if not input_path.exists():
                return f"❌ 输入目录不存在: {input_dir}"
            
            # 创建输出目录
            output_path.mkdir(parents=True, exist_ok=True)
            
            # 收集所有动作序列
            action_folders = [d for d in input_path.iterdir() if d.is_dir()]
            if not action_folders:
                return f"❌ 输入目录中没有找到动作文件夹: {input_dir}"
            
            # 获取第一帧来确定基准尺寸
            frame_width = None
            frame_height = None
            max_frames = 0  # 记录最大帧数，用于确定列数
            all_frames = []
            
            # 第一步：检查所有图片尺寸是否一致
            from PIL import Image
            for action_folder in sorted(action_folders):
                action_name = action_folder.name
                
                # 收集该动作的所有帧
                frames = sorted([
                    f for f in action_folder.glob("frame_*.png")
                    if f.is_file()
                ])
                
                if not frames:
                    frames = sorted([
                        f for f in action_folder.glob("frame_*.jpg")
                        if f.is_file()
                    ])
                
                if not frames:
                    logger.warning(f"动作文件夹 {action_name} 中没有找到帧文件")
                    continue
                
                # 检查每个图片的尺寸
                for frame_path in frames:
                    with Image.open(frame_path) as img:
                        w, h = img.size
                        if frame_width is None:
                            # 设置基准尺寸
                            frame_width, frame_height = w, h
                        elif w != frame_width or h != frame_height:
                            # 发现尺寸不一致
                            return f"""❌ 图片尺寸不一致！
                            
基准尺寸: {frame_width}x{frame_height}（首次在 {all_frames[0] if all_frames else '第一张图'} 中检测到）
不一致的图片: {frame_path}
实际尺寸: {w}x{h}

请确保所有动作序列的图片尺寸完全一致。"""
                
                # 记录最大帧数
                max_frames = max(max_frames, len(frames))
                all_frames.extend(frames)
            
            if not all_frames:
                return f"❌ 没有找到任何帧文件"
            
            # 使用最大帧数作为列数
            columns = max_frames
            
            # 构建配置（每个动作占一行）
            animations_config = {}
            current_row = 0
            
            for action_folder in sorted(action_folders):
                action_name = action_folder.name
                frames = sorted([f for f in action_folder.glob("frame_*.png")])
                
                if not frames:
                    frames = sorted([f for f in action_folder.glob("frame_*.jpg")])
                
                if frames:
                    frame_count = len(frames)
                    animations_config[action_name] = {
                        "row": current_row,
                        "frames": frame_count
                    }
                    # 每个动作占一行
                    current_row += 1
            
            config = {
                "name": input_path.name,
                "frame_width": frame_width,
                "frame_height": frame_height,
                "cols": columns,  # 使用最大帧数作为列数
                "rows": current_row,  # 动作数量即行数
                "padding": 0,  # 固定为0
                "background_color": background_color or [0, 0, 0, 0],
                "animations": animations_config  # 使用正确的格式
            }
            
            # 创建 SpriteSheetComposer
            composer = SpriteSheetComposer(config)
            
            # 准备临时输入目录（按动作分组）
            temp_input_dir = output_path / "_temp_frames"
            temp_input_dir.mkdir(exist_ok=True)
            
            # 为每个动作创建子目录并复制帧
            import shutil
            for action_folder in sorted(action_folders):
                action_name = action_folder.name
                frames = sorted([f for f in action_folder.glob("frame_*.png")])
                
                if frames:
                    # 创建动作子目录
                    action_temp_dir = temp_input_dir / action_name
                    action_temp_dir.mkdir(exist_ok=True)
                    
                    # 复制帧并重命名为 001.png, 002.png 格式
                    for i, frame_path in enumerate(frames, 1):
                        target_path = action_temp_dir / f"{i:03d}.png"
                        shutil.copy2(frame_path, target_path)
            
            # 生成精灵表
            output_file = output_path / "spritesheet.png"
            result = composer.create_sprite_sheet(
                str(temp_input_dir),
                str(output_file)
            )
            
            # 清理临时目录
            import shutil
            shutil.rmtree(temp_input_dir)
            
            if result["success"]:
                
                response_text = f"""✅ 精灵表生成成功！

输入目录: {input_dir}
动作数量: {len(animations_config)}
动作列表: {', '.join(animations_config.keys())}

输出文件:
- 精灵表: {output_file}
- 配置文件: {result['config_path']}"""
                    
                response_text += f"""

精灵表信息:
- 处理帧数: {result['processed_frames']}
- 缺失帧数: {result['missing_frames']}
- 精灵表尺寸: {result['sheet_width']}x{result['sheet_height']}
- 每帧尺寸: {frame_width}x{frame_height}
- 网格布局: {columns}列（最大帧数） x {current_row}行（动作数）

动画序列:"""
                for action, info in animations_config.items():
                    response_text += f"\n  - {action}: 第{info['row']}行, {info['frames']}帧"
                
                return response_text
            else:
                # 清理临时目录（如果生成失败）
                if temp_input_dir.exists():
                    import shutil
                    shutil.rmtree(temp_input_dir)
                return f"❌ {result['message']}"
                
        except Exception as e:
            logger.error(f"处理精灵图失败: {e}")
            return f"❌ 处理失败: {str(e)}"