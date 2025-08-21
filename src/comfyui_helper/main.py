#!/usr/bin/env python3
"""
ComfyUI Helper MCP Server 主入口
使用 FastMCP 简化实现
"""

import logging
from pathlib import Path
from mcp.server.fastmcp import FastMCP

from .sprite_composer import SpriteSheetComposer

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
        input_frames_dir = project_path / "input_frames"
        output_dir = project_path / "output"
        
        # 检查必要文件和目录
        if not input_frames_dir.exists():
            return f"❌ 未找到输入帧目录: {input_frames_dir}"
        
        # 创建输出目录
        output_dir.mkdir(exist_ok=True)
        
        # 加载配置
        composer = SpriteSheetComposer()
        if config_file.exists():
            config = composer.load_config_file(str(config_file))
            composer = SpriteSheetComposer(config)
            logger.info(f"已加载配置文件: {config_file}")
        else:
            logger.info("使用默认配置")
        
        # 生成输出文件名
        project_name = project_path.name
        output_path = output_dir / f"{project_name}_spritesheet.png"
        
        # 创建精灵表
        result = composer.create_sprite_sheet(
            str(input_frames_dir),
            str(output_path),
            generate_preview
        )
        
        if result["success"]:
            response_text = f"""✅ {result['message']}

项目: {project_name}
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


# 未来可以继续添加工具
# @mcp.tool()
# def another_tool(param1: str) -> str:
#     """另一个工具的描述"""
#     return f"处理: {param1}"


if __name__ == "__main__":
    logger.info("ComfyUI Helper MCP Server 已启动 (FastMCP)")
    mcp.run()