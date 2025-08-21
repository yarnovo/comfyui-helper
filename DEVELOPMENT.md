# 开发指南

## 架构设计

本项目使用 **FastMCP** 框架，这是 MCP Python SDK 提供的高级 API，让添加新工具变得极其简单。

```
src/comfyui_helper/
├── main.py              # 主文件，包含所有工具定义
├── sprite_composer.py   # 精灵图处理核心逻辑
└── __main__.py          # 程序入口
```

## 添加新工具的步骤

使用 FastMCP，添加新工具只需要一个装饰器！

### 1. 在 main.py 中添加工具函数

```python
# src/comfyui_helper/main.py

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

## 示例工具

参考 `tools/example_tool.py` 查看完整示例，包括：
- 多个工具方法
- 资源定义
- 提示词模板
- 参数验证
- 错误处理