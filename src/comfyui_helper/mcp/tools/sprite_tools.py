"""
精灵图相关的 MCP 工具
"""

import json
import logging
from pathlib import Path
from ...core.sprite_composer import SpriteSheetComposer

logger = logging.getLogger(__name__)


def register_sprite_tools(mcp):
    """注册精灵图相关的 MCP 工具"""
    
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
- 帧数量: {result['frame_count']}
- 精灵表尺寸: {result['sheet_width']}x{result['sheet_height']}
- 每帧尺寸: {result['frame_width']}x{result['frame_height']}
- 网格布局: {result['columns']}列 x {result['rows']}行"""
                
                return response_text
            else:
                return f"❌ {result['message']}"
                
        except Exception as e:
            logger.error(f"处理精灵图项目失败: {e}")
            return f"❌ 处理失败: {str(e)}"