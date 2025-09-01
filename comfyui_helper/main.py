#!/usr/bin/env python3
"""
ComfyUI Helper MCP Server 主入口
"""

import logging
from .mcp import initialize_mcp_server

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化并获取 MCP 服务器实例
mcp = initialize_mcp_server()

# 主函数
def main():
    """运行 MCP 服务器"""
    logger.info("正在启动 ComfyUI Helper MCP 服务器...")
    mcp.run()

if __name__ == "__main__":
    main()