# ComfyUI Helper

一个提供游戏开发和 AI 图像处理辅助功能的 MCP (Model Context Protocol) 服务器项目。

## 快速开始

### 前置要求

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (Python 包管理器)

### 安装

```bash
# 克隆项目
git clone <repository-url>
cd comfyui-helper

# 安装依赖
uv sync

# 安装包为可编辑模式
uv pip install -e .
```

**注意**：`-e` 参数表示可编辑安装，这样修改源代码后无需重新安装即可生效。

### 在 Claude Desktop 中使用

1. 编辑 Claude Desktop 配置文件：
   - Windows: `~/AppData/Roaming/Claude/claude_desktop_config.json`
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

2. 添加以下配置（替换为您的实际项目路径）：

```json
{
  "mcpServers": {
    "comfyui-helper": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/comfyui-helper",
        "run",
        "python",
        "-m",
        "comfyui_helper"
      ],
      "env": {}
    }
  }
}
```

3. 重启 Claude Desktop 即可使用

## 可用工具

### 🎮 精灵图拼接工具

将单个精灵帧图片拼接成游戏引擎可用的精灵表格式。

**使用示例：**
```
compose_sprite_sheet(
  project_dir="/path/to/sprite_project",
  generate_preview=true
)
```

详细文档请参考：[精灵图工具文档](src/comfyui_helper/README.md)

## 项目结构

```
comfyui-helper/
├── .mcp.json              # MCP 本地配置
├── pyproject.toml         # 项目配置
├── README.md              # 本文档
└── src/
    └── comfyui_helper/
        ├── README.md      # 工具详细文档
        ├── __init__.py    
        ├── __main__.py    # 入口点
        ├── server.py      # MCP 服务器
        └── sprite_composer.py  # 精灵图处理模块
```

## 开发指南

### 运行测试

```bash
# 直接运行 MCP 服务器
uv run python -m comfyui_helper
```

### 开发时的注意事项

- **源代码修改**：由于使用了可编辑安装（`-e`），修改代码后直接重启服务即可，无需重新安装
- **添加新依赖**：修改 `pyproject.toml` 后需要运行 `uv sync` 和 `uv pip install -e .`
- **包结构变更**：如果改变了包结构（添加新模块等），需要重新运行 `uv pip install -e .`

### 添加新工具

1. 在 `src/comfyui_helper/` 下创建新的模块
2. 在 `server.py` 的 `list_tools()` 中注册工具
3. 在 `call_tool()` 中实现工具逻辑
4. 更新相关文档

## 故障排查

### Windows 路径问题
- 使用正斜杠 `/` 或双反斜杠 `\\` 
- 确保使用绝对路径

### 依赖问题
```bash
# 重新安装依赖
uv sync --refresh

# 如果模块导入失败
uv pip install -e .
```

### MCP 连接问题
- 确认 Claude Desktop 已重启
- 检查配置文件 JSON 格式是否正确
- 查看日志：`~/Library/Logs/Claude/mcp.log` (macOS)

## 许可证

MIT

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系方式

如有问题或建议，请通过 GitHub Issues 联系。