"""
MCP (Model Context Protocol) 服务器模块
"""

from mcp.server.fastmcp import FastMCP

# 创建全局 MCP 服务器实例
mcp_server = FastMCP("comfyui-helper")

# 导入并注册所有工具和资源
from .tools import register_tools
from .resources import register_resources

def initialize_mcp_server():
    """初始化 MCP 服务器，注册所有工具和资源"""
    register_tools(mcp_server)
    register_resources(mcp_server)
    return mcp_server