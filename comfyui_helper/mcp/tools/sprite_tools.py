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
        columns: int = 8,
        padding: int = 0,
        background_color: Optional[list] = None
    ) -> str:
        """
        处理包含多个动作序列的精灵图文件夹，每个子文件夹代表一个动作
        
        Args:
            input_dir: 输入文件夹路径，包含多个动作子文件夹
            output_dir: 输出文件夹路径
            columns: 精灵表的列数（默认8列）
            padding: 帧之间的间距（默认0）
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
            
            # 收集所有帧并记录动作信息
            all_frames = []
            animation_sequences = {}
            current_index = 0
            
            # 获取第一帧来确定尺寸
            frame_width = None
            frame_height = None
            
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
                
                # 获取帧尺寸
                if frame_width is None:
                    from PIL import Image
                    with Image.open(frames[0]) as img:
                        frame_width, frame_height = img.size
                
                # 记录动作序列
                frame_count = len(frames)
                animation_sequences[action_name] = list(range(current_index, current_index + frame_count))
                current_index += frame_count
                
                # 添加到总帧列表
                all_frames.extend(frames)
            
            if not all_frames:
                return f"❌ 没有找到任何帧文件"
            
            # 构建配置
            config = {
                "name": input_path.name,
                "frame_width": frame_width,
                "frame_height": frame_height,
                "columns": columns,
                "padding": padding,
                "background_color": background_color or [0, 0, 0, 0],
                "animation": {
                    "sequences": animation_sequences
                }
            }
            
            # 创建 SpriteSheetComposer
            composer = SpriteSheetComposer(config)
            
            # 准备临时输入目录（复制所有帧到统一目录）
            temp_input_dir = output_path / "_temp_frames"
            temp_input_dir.mkdir(exist_ok=True)
            
            # 复制并重命名所有帧
            for i, frame_path in enumerate(all_frames):
                import shutil
                target_path = temp_input_dir / f"frame_{i:04d}.png"
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
动作数量: {len(animation_sequences)}
动作列表: {', '.join(animation_sequences.keys())}

输出文件:
- 精灵表: {output_file}
- 配置文件: {config_file}"""
                    
                response_text += f"""

精灵表信息:
- 总帧数: {result['frame_count']}
- 精灵表尺寸: {result['sheet_width']}x{result['sheet_height']}
- 每帧尺寸: {frame_width}x{frame_height}
- 网格布局: {result['columns']}列 x {result['rows']}行

动画序列:"""
                for action, indices in animation_sequences.items():
                    response_text += f"\n  - {action}: 帧 {indices[0]}-{indices[-1]} (共{len(indices)}帧)"
                
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