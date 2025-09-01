"""
MCP 资源模块
"""

from .sprite_resources import register_sprite_resources
from .guide_resources import register_guide_resources


def register_resources(mcp):
    """注册所有 MCP 资源"""
    register_sprite_resources(mcp)
    register_guide_resources(mcp)