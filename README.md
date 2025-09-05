# ComfyUI Helper

一个集成了 AI 图像处理、游戏开发工具和 MCP (Model Context Protocol) 服务的多功能助手工具。支持背景移除、图像缩放、精灵图合成和 GIF 制作等功能。

## 快速开始

### 前置要求

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (Python 包管理器)

### 安装

#### 开发模式安装（推荐）

```bash
# 克隆项目
git clone https://github.com/your-username/comfyui-helper.git
cd comfyui-helper

# 安装依赖
uv sync

# 安装包为可编辑模式（开发用）
uv pip install -e .
```

#### 全局工具安装

```bash
# 全局安装 CLI 工具
uv tool install comfyui-helper

# 或从本地安装
uv tool install /path/to/comfyui-helper
```

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

## 功能特性

### 🎨 图像处理工具

#### 背景移除
- 使用先进的 RMBG-2.0 模型
- 支持单张和批量处理
- 可选择透明或白色背景
- Alpha 通道阈值调节

#### 图像缩放
- 支持多种重采样算法（nearest/bilinear/bicubic/lanczos）
- 保持宽高比缩放
- 自定义目标尺寸
- JPEG 质量控制

### 🎮 游戏开发工具

#### 精灵图合成
- 自动拼接动画帧序列
- 生成标准精灵表格式
- 自动创建动画配置文件
- 支持多个动作序列

### 🎬 GIF 制作器
- Web GUI 界面
- 视频转 GIF
- 自定义帧率和尺寸
- 实时预览

### 📡 MCP 服务集成

在 Claude Desktop 中可直接调用以下工具：
- `compose_sprite_sheet` - 合成精灵图表
- `scale_image` - 缩放图像
- `remove_background` - 移除背景
- `batch_remove_background` - 批量移除背景

## 命令行使用

### CLI 工具

```bash
# 启动 GIF 制作器 Web GUI
cfh gif-maker

# 查看帮助
cfh --help
```

### Python API

```python
from comfyui_helper.core import BackgroundRemover, ImageScaler, SpriteComposer

# 移除背景
remover = BackgroundRemover()
result = await remover.process_image("input.jpg", "output.png")

# 缩放图像
scaler = ImageScaler()
scaler.scale_image("input.jpg", scale_factor=2.0)

# 合成精灵图
composer = SpriteComposer()
composer.create_sprite_sheet("sprites_dir", "output_dir")
```

## 项目结构

```
comfyui-helper/
├── comfyui_helper/
│   ├── cli/               # 命令行工具
│   │   ├── main.py        # CLI 入口
│   │   └── gif_maker_gui.py
│   ├── core/              # 核心功能模块
│   │   ├── background_remover.py
│   │   ├── image_scaler.py
│   │   ├── sprite_composer.py
│   │   ├── gif_maker.py
│   │   └── video_frame_extractor.py
│   └── mcp/               # MCP 服务
│       ├── tools/         # MCP 工具定义
│       └── resources/     # MCP 资源
├── examples/              # 示例项目
├── docs/                  # 文档
├── pyproject.toml         # 项目配置
└── README.md              # 本文档
```

## 开发指南

### 运行和测试

```bash
# 运行 MCP 服务器
uv run python -m comfyui_helper

# 运行 CLI 工具
uv run cfh gif-maker

# 开发模式调试
uv run python -m comfyui_helper.cli.gif_maker_gui
```

### 添加新功能

1. **核心功能**：在 `comfyui_helper/core/` 下创建模块
2. **MCP 工具**：在 `comfyui_helper/mcp/tools/` 下添加并注册
3. **CLI 命令**：在 `comfyui_helper/cli/main.py` 中添加子命令
4. 更新测试和文档

### 依赖管理

```bash
# 添加新依赖
uv add package-name

# 同步依赖
uv sync

# 重新安装（开发模式）
uv pip install -e .
```

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