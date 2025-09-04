# 开发指南

## 架构设计

本项目使用 **FastMCP** 框架，这是 MCP Python SDK 提供的高级 API，让添加新工具变得极其简单。

```
comfyui_helper/
├── __init__.py          # 包初始化
├── __main__.py          # MCP Server 入口点
├── main.py              # MCP Server 主文件
├── cli/                 # 命令行工具
│   ├── __init__.py
│   ├── main.py          # CLI 统一入口
│   └── gif_maker_gui.py # GIF 制作器 GUI
├── core/                # 核心功能模块
│   ├── __init__.py
│   ├── gif_maker.py     # GIF 生成器
│   ├── sprite_composer.py # 精灵图处理
│   └── bg_remover.py    # 背景移除工具
└── mcp/                 # MCP 相关
    ├── __init__.py
    └── tools/           # MCP 工具定义
```

## 添加新工具的步骤

使用 FastMCP，添加新工具只需要一个装饰器！

### 1. 在 mcp/__init__.py 中添加工具函数

```python
# comfyui_helper/mcp/__init__.py

@mcp.tool()
def your_tool_name(param1: str, param2: int = 10) -> str:
    """
    工具的描述文档（这会成为工具的 description）
    
    Args:
        param1: 第一个参数的说明
        param2: 第二个参数的说明（有默认值）
        
    Returns:
        返回值说明
    """
    # 您的业务逻辑
    result = f"处理 {param1}，数量：{param2}"
    return result
```

就这么简单！FastMCP 会自动：
- 从函数签名生成参数 schema
- 从 docstring 提取描述
- 处理类型转换和验证
- 生成 MCP 协议响应

### 2. 测试

```bash
# 重启服务测试
uv run python -m comfyui_helper
```

## 工具开发最佳实践

### 工具设计原则

1. **单一职责**：每个工具类专注于一个功能领域
2. **清晰的接口**：工具名称和参数要有描述性
3. **错误处理**：返回友好的错误信息
4. **日志记录**：使用 logging 记录关键操作

### 返回格式

MCP 工具应返回标准格式：

```python
# 文本响应
[{"type": "text", "text": "响应内容"}]

# 错误响应
[{"type": "text", "text": "❌ 错误信息"}]

# 成功响应
[{"type": "text", "text": "✅ 成功信息"}]
```

### 可选功能

工具可以提供资源和提示词：

```python
def get_resources(self) -> List[Dict[str, Any]]:
    """定义资源"""
    return [
        {
            "uri": "your://resource",
            "name": "资源名称",
            "description": "资源描述",
            "mimeType": "application/json"
        }
    ]

def get_prompts(self) -> List[Dict[str, Any]]:
    """定义提示词模板"""
    return [
        {
            "name": "your_prompt",
            "description": "提示词描述",
            "arguments": [...]
        }
    ]
```

## 调试技巧

### 日志

使用 Python logging：

```python
import logging
logger = logging.getLogger(__name__)

logger.info("信息日志")
logger.error(f"错误: {e}")
```

### 本地测试

创建测试脚本：

```python
# test_tool.py
import asyncio
from src.comfyui_helper.tools.your_tool import YourTool

async def test():
    tool = YourTool()
    result = await tool.handle_tool("your_tool_name", {"param1": "test"})
    print(result)

asyncio.run(test())
```

## 常见模式

### 文件处理工具

```python
from pathlib import Path

async def _process_file(self, arguments):
    file_path = Path(arguments.get("file_path"))
    
    if not file_path.exists():
        return f"❌ 文件不存在: {file_path}"
    
    # 处理文件
    with open(file_path, 'r') as f:
        content = f.read()
    
    return f"✅ 处理完成"
```

### 异步操作

```python
import aiohttp

async def _fetch_data(self, url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
```

### 配置管理

```python
import json

def load_config(self, config_path):
    with open(config_path, 'r') as f:
        return json.load(f)
```

## 发布前检查清单

- [ ] 工具已在 `main.py` 中注册
- [ ] 所有参数都有清晰的描述
- [ ] 错误处理完善
- [ ] 添加了适当的日志
- [ ] 更新了 README 文档
- [ ] 测试通过

## CLI 工具使用

### 全局安装

本项目提供了 `cfh` 命令行工具，可以全局使用：

```bash
# 使用 uv tool 全局安装
uv tool install /path/to/comfyui-helper

# 或者在开发模式下安装（仅虚拟环境）
uv pip install -e .
source .venv/bin/activate
```

### 使用 CLI 工具

```bash
# 查看帮助
cfh --help

# 启动 GIF 制作器 GUI
cfh gif-maker
```

### 添加新的 CLI 命令

1. 在 `cli/` 目录下创建新的模块
2. 在 `cli/main.py` 中添加新的子命令：

```python
# comfyui_helper/cli/main.py

def run_your_tool():
    """运行你的工具"""
    from .your_tool import main as tool_main
    tool_main()

# 在 argparse 中添加子命令
your_parser = subparsers.add_parser(
    'your-tool',
    help='你的工具描述'
)
```

3. 重新安装以更新命令：

```bash
# 开发模式
uv pip install -e .

# 全局安装
uv tool install --force /path/to/comfyui-helper
```

### 注意事项

- `uv tool install` 不支持开发模式，代码修改后需要重新安装
- 开发时建议使用虚拟环境中的命令：`.venv/bin/cfh`
- 全局命令安装在 `~/.local/bin/cfh`

## 示例工具

参考现有工具实现：
- `core/gif_maker.py` - GIF 生成器
- `core/bg_remover.py` - 背景移除工具
- `core/sprite_composer.py` - 精灵图处理