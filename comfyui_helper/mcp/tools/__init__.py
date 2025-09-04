"""
MCP 工具模块
"""

from .sprite_tools import register_sprite_tools
from .image_tools import register_image_tools


def register_tools(mcp):
    """注册所有 MCP 工具"""
    register_sprite_tools(mcp)
    register_image_tools(mcp)