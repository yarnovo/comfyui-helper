#!/usr/bin/env python3
"""带 Web GUI 的 GIF 动画生成工具"""

import os
# 设置环境变量去除代理，确保 localhost 可访问
os.environ['NO_PROXY'] = 'localhost,127.0.0.1'
os.environ['no_proxy'] = 'localhost,127.0.0.1'

import gradio as gr
from pathlib import Path
from PIL import Image
from typing import List, Dict, Optional, Tuple
import logging
import json
from datetime import datetime
import re
import sys
import threading
import time
import io
import tempfile

# 支持直接运行
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from src.comfyui_helper.cli.gif_maker import GifMaker
else:
    from .gif_maker import GifMaker

logger = logging.getLogger(__name__)


class GifMakerGUI:
    """GIF 生成器 Web GUI"""
    
    def __init__(self, input_dir: str):
        """
        初始化 GUI
        
        Args:
            input_dir: 包含图片的输入目录
        """
        self.input_dir = Path(input_dir)
        self.gif_maker = GifMaker()
        self.image_files = []
        self.should_exit = False
        self.app = None
        self.current_gif_data = None  # 存储当前生成的 GIF 数据
        self.current_gif_config = None  # 存储当前 GIF 配置
        
        # 加载并排序图片文件
        self._load_images()
    
    def _load_images(self):
        """加载目录中的所有图片文件"""
        logger.debug(f"_load_images开始，input_dir: {self.input_dir}")
        
        # 确保 input_dir 是 Path 对象
        if not isinstance(self.input_dir, Path):
            logger.debug(f"将input_dir从字符串转换为Path对象: {self.input_dir}")
            self.input_dir = Path(self.input_dir)
            
        # 支持的图片格式
        extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp']
        logger.debug(f"支持的图片格式: {extensions}")
        
        # 查找所有图片文件
        all_images = []
        for ext in extensions:
            found = list(self.input_dir.glob(f"*{ext}"))
            if found:
                logger.debug(f"找到 {len(found)} 个 {ext} 文件")
                all_images.extend(found)
            found_upper = list(self.input_dir.glob(f"*{ext.upper()}"))
            if found_upper:
                logger.debug(f"找到 {len(found_upper)} 个 {ext.upper()} 文件")
                all_images.extend(found_upper)
        
        logger.debug(f"总共找到 {len(all_images)} 个图片文件")
        
        # 过滤出数字命名的文件并排序
        numeric_pattern = re.compile(r'^(\d+)\.')
        numeric_images = []
        
        for img_path in all_images:
            match = numeric_pattern.match(img_path.name)
            if match:
                number = int(match.group(1))
                numeric_images.append((number, img_path))
        
        # 按数字排序
        numeric_images.sort(key=lambda x: x[0])
        self.image_files = [str(path) for _, path in numeric_images]
        
        logger.info(f"找到 {len(self.image_files)} 个数字命名的图片文件")
    
    def load_images(self):
        """公共方法：重新加载图片"""
        self._load_images()
    
    def get_all_images(self) -> List[str]:
        """获取所有图片路径列表"""
        return self.image_files.copy()
    
    def set_start_image(self, selected_images) -> Tuple[str, str]:
        """设置开始图片"""
        logger.info(f"set_start_image received: {selected_images}, type: {type(selected_images)}")
        
        if not selected_images:
            return "", "未设置"
        
        # Gradio Gallery 可能返回不同格式
        # 1. 索引列表 [0] 
        # 2. 文件路径列表
        # 3. Event SelectData 对象
        
        # 如果是 SelectData 对象，获取索引
        if hasattr(selected_images, 'index'):
            selected_index = selected_images.index
            if 0 <= selected_index < len(self.image_files):
                img_path = self.image_files[selected_index]
                return str(img_path), f"{Path(img_path).name}"
        
        # 如果是列表
        if isinstance(selected_images, list) and len(selected_images) > 0:
            first_item = selected_images[0]
            
            # 如果是索引
            if isinstance(first_item, int) and 0 <= first_item < len(self.image_files):
                img_path = self.image_files[first_item]
                return str(img_path), f"{Path(img_path).name}"
            
            # 如果是文件路径
            if isinstance(first_item, str):
                for idx, file_path in enumerate(self.image_files):
                    if file_path == first_item or Path(file_path).name == Path(first_item).name:
                        return str(file_path), f"{Path(file_path).name}"
        
        return "", "未设置"
    
    def set_end_image(self, selected_images) -> Tuple[str, str]:
        """设置结束图片"""
        logger.info(f"set_end_image received: {selected_images}, type: {type(selected_images)}")
        
        if not selected_images:
            return "", "未设置"
        
        # 如果是 SelectData 对象，获取索引
        if hasattr(selected_images, 'index'):
            selected_index = selected_images.index
            if 0 <= selected_index < len(self.image_files):
                img_path = self.image_files[selected_index]
                return str(img_path), f"{Path(img_path).name}"
        
        # 如果是列表
        if isinstance(selected_images, list) and len(selected_images) > 0:
            first_item = selected_images[0]
            
            # 如果是索引
            if isinstance(first_item, int) and 0 <= first_item < len(self.image_files):
                img_path = self.image_files[first_item]
                return str(img_path), f"{Path(img_path).name}"
            
            # 如果是文件路径
            if isinstance(first_item, str):
                for idx, file_path in enumerate(self.image_files):
                    if file_path == first_item or Path(file_path).name == Path(first_item).name:
                        return str(file_path), f"{Path(file_path).name}"
        
        return "", "未设置"
    
    def update_selection(self, start_path: str, end_path: str) -> Tuple[str, List]:
        """根据开始和结束图片更新选择范围"""
        if not start_path or not end_path:
            return "请设置开始和结束图片", []
        
        try:
            start_idx = self.image_files.index(start_path)
            end_idx = self.image_files.index(end_path)
            
            if start_idx > end_idx:
                # 交换顺序
                start_idx, end_idx = end_idx, start_idx
            
            # 获取范围内的所有文件
            selected_files = self.image_files[start_idx:end_idx + 1]
            
            info_text = f"已选择 {len(selected_files)} 张图片\n"
            info_text += f"从 {Path(self.image_files[start_idx]).name} 到 {Path(self.image_files[end_idx]).name}"
            
            return info_text, selected_files
            
        except ValueError as e:
            return f"错误：{str(e)}", []
    
    def preview_gif(self, selected_files: List, duration: int, 
                    loop: int, optimize: bool, resize_width: Optional[int], 
                    resize_height: Optional[int], progress=gr.Progress()) -> Tuple[str, str]:
        """在内存中生成 GIF 预览"""
        if not selected_files:
            return None, "请先选择图片"
        
        try:
            progress(0, desc="准备生成预览...")
            
            # 确定输出尺寸
            resize_to = None
            if resize_width and resize_height:
                resize_to = (int(resize_width), int(resize_height))
            
            progress(0.3, desc="正在生成 GIF...")
            
            # 使用临时文件生成 GIF（因为 PIL 需要文件路径）
            with tempfile.NamedTemporaryFile(suffix='.gif', delete=False) as tmp_file:
                tmp_path = tmp_file.name
                
                # 创建 GIF
                result = self.gif_maker.create_gif(
                    image_paths=selected_files,
                    output_path=tmp_path,
                    duration=duration,
                    loop=loop,
                    optimize=optimize,
                    resize_to=resize_to
                )
                
                if result["success"]:
                    progress(0.8, desc="准备预览...")
                    
                    # 保存配置信息供后续保存使用
                    self.current_gif_config = {
                        "created_at": datetime.now().isoformat(),
                        "frame_count": result["frame_count"],
                        "duration_per_frame": duration,
                        "total_duration_ms": result["total_duration"],
                        "loop": loop,
                        "optimize": optimize,
                        "dimensions": {
                            "width": result["dimensions"][0],
                            "height": result["dimensions"][1]
                        },
                        "file_size_bytes": result["file_size"],
                        "start_image": Path(selected_files[0]).name if selected_files else None,
                        "end_image": Path(selected_files[-1]).name if selected_files else None,
                        "input_images": [Path(f).name for f in selected_files],
                        "selected_files": selected_files
                    }
                    
                    # 读取 GIF 数据到内存
                    with open(tmp_path, 'rb') as f:
                        self.current_gif_data = f.read()
                    
                    progress(1.0, desc="完成！")
                    
                    # 生成结果信息
                    info_text = f"""✅ GIF 预览生成成功！
                    
大小：{result['file_size']/1024:.1f} KB
尺寸：{result['dimensions'][0]}x{result['dimensions'][1]}
帧数：{result['frame_count']}
总时长：{result['total_duration']/1000:.1f} 秒
循环：{'无限' if loop == 0 else f'{loop} 次'}

提示：点击"保存 GIF"按钮可以保存到本地"""
                    
                    # 返回临时文件路径（不删除，让 Gradio 显示）
                    # 临时文件会被系统自动清理
                    return tmp_path, info_text
                else:
                    return None, f"❌ 生成失败：{result['message']}"
                    
        except Exception as e:
            logger.error(f"生成 GIF 预览失败：{e}")
            return None, f"❌ 错误：{str(e)}"
    
    def save_gif(self, output_dir: str = None) -> str:
        """保存当前的 GIF 到指定目录"""
        if not self.current_gif_data:
            return "❌ 没有可保存的 GIF，请先生成预览"
        
        try:
            # 使用默认输出目录或指定目录
            if output_dir:
                save_dir = Path(output_dir)
            else:
                save_dir = self.input_dir / "gif_output"
            
            save_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            gif_name = f"animation_{timestamp}.gif"
            gif_path = save_dir / gif_name
            
            # 保存 GIF 文件
            with open(gif_path, 'wb') as f:
                f.write(self.current_gif_data)
            
            # 保存配置文件
            if self.current_gif_config:
                config_name = f"config_{timestamp}.json"
                config_path = save_dir / config_name
                
                # 添加保存信息
                config = self.current_gif_config.copy()
                config["saved_at"] = datetime.now().isoformat()
                config["gif_file"] = gif_name
                config["output_dir"] = str(save_dir)
                
                # 移除临时数据
                config.pop("selected_files", None)
                
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                
                return f"""✅ GIF 已保存！

文件：{gif_path}
配置：{config_path}
大小：{len(self.current_gif_data)/1024:.1f} KB"""
            
            return f"✅ GIF 已保存到：{gif_path}"
            
        except Exception as e:
            logger.error(f"保存 GIF 失败：{e}")
            return f"❌ 保存失败：{str(e)}"
    
    
    def create_interface(self):
        """创建 Gradio 界面"""
        with gr.Blocks(title="GIF 生成器", theme=gr.themes.Soft()) as self.app:
            gr.Markdown("# 🎬 GIF 动画生成器")
            
            # 文件夹选择区域
            with gr.Row():
                folder_input = gr.Textbox(
                    label="📁 图片文件夹路径",
                    value="",
                    placeholder="输入图片文件夹路径",
                    scale=4
                )
                load_folder_btn = gr.Button("🔄 加载文件夹", variant="primary", scale=1)
            
            # 状态显示
            status_display = gr.Markdown("📌 请选择包含图片的文件夹")
            
            # 存储当前选择的状态
            start_index = gr.State(-1)
            end_index = gr.State(-1)
            current_selection = gr.State([])
            
            with gr.Row():
                # 左侧：图片选择
                with gr.Column(scale=1):
                    gr.Markdown("### 📁 选择图片")
                    
                    # 所有图片库
                    all_images_gallery = gr.Gallery(
                        value=self.get_all_images(),
                        label="点击选择图片",
                        columns=4,
                        rows=4,
                        height=400,
                        interactive=True,
                        type="filepath",
                        show_label=True
                    )
                    
                    # 设置按钮
                    with gr.Row():
                        set_start_btn = gr.Button("📍 设为开始", variant="primary", scale=1)
                        set_end_btn = gr.Button("🎯 设为结束", variant="primary", scale=1)
                    
                    # 显示当前选择（图片预览和文件名）
                    with gr.Row():
                        with gr.Column(scale=1):
                            start_preview = gr.Image(label="开始图片", height=100, interactive=False)
                            start_filename = gr.Textbox(label="文件名", value="未设置", interactive=False)
                        with gr.Column(scale=1):
                            end_preview = gr.Image(label="结束图片", height=100, interactive=False)
                            end_filename = gr.Textbox(label="文件名", value="未设置", interactive=False)
                    
                    # 每帧时长（简化参数）
                    duration = gr.Slider(
                        minimum=50,
                        maximum=500,
                        value=100,
                        step=50,
                        label="速度 (毫秒/帧)"
                    )
                
                # 右侧：预览
                with gr.Column(scale=1):
                    gr.Markdown("### 📸 预览")
                    
                    # 生成按钮
                    preview_gif_btn = gr.Button("🎬 生成 GIF 预览", variant="primary", size="lg")
                    
                    # GIF 预览
                    gif_output = gr.Image(
                        label="GIF 动画",
                        type="filepath"
                    )
            
            # 事件绑定（简化版）
            
            # 存储当前选中的图片索引
            current_selected_index = gr.State(-1)
            
            # Gallery 选择事件
            def on_gallery_select(evt: gr.SelectData):
                return evt.index if evt else -1
            
            all_images_gallery.select(
                fn=on_gallery_select,
                outputs=[current_selected_index]
            )
            
            # 设为开始图片
            def set_start(idx):
                if idx >= 0 and idx < len(self.image_files):
                    file_path = self.image_files[idx]
                    file_name = Path(file_path).name
                    return idx, file_path, file_name  # 返回索引、图片路径和文件名
                return -1, None, "未设置"  # 返回默认值
            
            # 设为结束图片  
            def set_end(idx):
                if idx >= 0 and idx < len(self.image_files):
                    file_path = self.image_files[idx]
                    file_name = Path(file_path).name
                    return idx, file_path, file_name  # 返回索引、图片路径和文件名
                return -1, None, "未设置"  # 返回默认值
            
            # 更新选择范围（返回选中的文件列表）
            def update_range(start_idx, end_idx):
                if start_idx >= 0 and end_idx >= 0:
                    if start_idx > end_idx:
                        start_idx, end_idx = end_idx, start_idx
                    selected = self.image_files[start_idx:end_idx + 1]
                    return selected
                return []
            
            # 生成简化的 GIF
            def generate_gif(selected_files, duration):
                if not selected_files:
                    return None
                
                try:
                    # 使用临时文件
                    import tempfile
                    with tempfile.NamedTemporaryFile(suffix='.gif', delete=False) as tmp:
                        result = self.gif_maker.create_gif(
                            image_paths=selected_files,
                            output_path=tmp.name,
                            duration=duration,
                            loop=0,  # 无限循环
                            optimize=True,
                            resize_to=None
                        )
                        if result["success"]:
                            return tmp.name
                except Exception as e:
                    logger.error(f"生成 GIF 失败：{e}")
                return None
            
            # 点击设为开始
            set_start_btn.click(
                fn=set_start,
                inputs=[current_selected_index],
                outputs=[start_index, start_preview, start_filename]  # 输出索引、图片和文件名
            ).then(
                fn=update_range,
                inputs=[start_index, end_index],
                outputs=[current_selection]  # 只输出当前选择的文件列表
            )
            
            # 点击设为结束
            set_end_btn.click(
                fn=set_end,
                inputs=[current_selected_index],
                outputs=[end_index, end_preview, end_filename]  # 输出索引、图片和文件名
            ).then(
                fn=update_range,
                inputs=[start_index, end_index],
                outputs=[current_selection]  # 只输出当前选择的文件列表
            )
            
            # 生成 GIF
            preview_gif_btn.click(
                fn=generate_gif,
                inputs=[current_selection, duration],
                outputs=[gif_output]
            )
            
            # 加载新文件夹功能
            def load_new_folder(folder_path):
                """加载新的图片文件夹"""
                try:
                    from pathlib import Path
                    import platform
                    
                    logger.debug(f"开始加载文件夹，原始输入: '{folder_path}'")
                    folder_path = folder_path.strip()
                    logger.debug(f"去除空格后: '{folder_path}'")
                    
                    # Windows路径到WSL路径的转换
                    def convert_windows_to_wsl_path(path_str):
                        """将Windows路径转换为WSL路径"""
                        logger.debug(f"检查是否需要转换路径: '{path_str}'")
                        # 检查是否是Windows路径格式 (C:\ 或 C:/)
                        if len(path_str) >= 3 and path_str[1] == ':' and (path_str[2] == '\\' or path_str[2] == '/'):
                            # 获取盘符（转为小写）
                            drive_letter = path_str[0].lower()
                            logger.debug(f"检测到Windows路径，盘符: {drive_letter}")
                            # 获取路径部分，去掉 "C:" 或 "C:\"
                            path_part = path_str[2:] if path_str[2] in ['\\', '/'] else path_str[3:]
                            # 替换反斜杠为正斜杠
                            path_part = path_part.replace('\\', '/')
                            # 构建WSL路径
                            wsl_path = f"/mnt/{drive_letter}{path_part}"
                            logger.debug(f"转换后的WSL路径: '{wsl_path}'")
                            return wsl_path
                        logger.debug(f"不是Windows路径，保持原样")
                        return path_str
                    
                    # 如果在WSL环境中，尝试转换Windows路径
                    system_info = platform.uname().release
                    logger.debug(f"系统信息: {system_info}")
                    if 'microsoft' in system_info.lower() or 'WSL' in system_info:
                        original_path = folder_path
                        folder_path = convert_windows_to_wsl_path(folder_path)
                        if original_path != folder_path:
                            logger.info(f"转换Windows路径: {original_path} -> {folder_path}")
                    
                    if not folder_path:
                        return (
                            gr.update(),  # all_images_gallery
                            "❌ 请输入文件夹路径",  # status_display
                            -1,  # start_index
                            -1,  # end_index
                            [],  # current_selection
                            None,  # start_preview
                            "未设置",  # start_filename
                            None,  # end_preview
                            "未设置"  # end_filename
                        )
                    
                    folder = Path(folder_path)
                    logger.debug(f"创建Path对象: {folder}")
                    logger.debug(f"检查路径是否存在: {folder.exists()}")
                    
                    if not folder.exists():
                        logger.error(f"文件夹不存在: {folder_path}")
                        # 尝试列出父目录内容以帮助调试
                        parent = folder.parent
                        if parent.exists():
                            logger.debug(f"父目录 {parent} 存在")
                            try:
                                items = list(parent.iterdir())[:10]  # 只列出前10个
                                logger.debug(f"父目录内容示例: {items}")
                            except Exception as e:
                                logger.debug(f"无法列出父目录内容: {e}")
                        return (
                            gr.update(),
                            f"❌ 文件夹不存在：`{folder_path}`",
                            -1, -1, [], None, "未设置", None, "未设置"
                        )
                    
                    logger.debug(f"检查是否是目录: {folder.is_dir()}")
                    if not folder.is_dir():
                        logger.error(f"路径不是文件夹: {folder_path}")
                        return (
                            gr.update(),
                            f"❌ 路径不是文件夹：`{folder_path}`",
                            -1, -1, [], None, "未设置", None, "未设置"
                        )
                    
                    # 更新实例的属性
                    logger.info(f"更新input_dir: {str(folder)}")
                    self.input_dir = str(folder)
                    
                    logger.debug(f"调用load_images()方法")
                    self.load_images()
                    
                    logger.info(f"加载完成，找到 {len(self.image_files)} 个图片文件")
                    if self.image_files:
                        logger.debug(f"前5个文件: {self.image_files[:5]}")
                    
                    if not self.image_files:
                        logger.warning(f"文件夹中没有找到数字命名的图片")
                        # 列出文件夹内容以帮助调试
                        try:
                            all_files = list(folder.iterdir())[:20]
                            logger.debug(f"文件夹中的文件（前20个）: {all_files}")
                        except Exception as e:
                            logger.debug(f"无法列出文件夹内容: {e}")
                        return (
                            gr.update(value=[]),
                            f"⚠️ 文件夹中没有找到数字命名的图片：`{folder_path}`",
                            -1, -1, [], None, "未设置", None, "未设置"
                        )
                    
                    # 成功加载
                    logger.info(f"成功加载文件夹，准备更新Gallery")
                    gallery_images = self.get_all_images()
                    logger.debug(f"Gallery将显示 {len(gallery_images)} 个图片")
                    
                    return (
                        gr.update(value=gallery_images),  # 更新 gallery
                        f"✅ 已加载：`{self.input_dir}` - 找到 **{len(self.image_files)}** 个图片文件",
                        -1,  # 重置 start_index
                        -1,  # 重置 end_index
                        [],  # 清空 current_selection
                        None,  # 清空 start_preview
                        "未设置",  # 重置 start_filename
                        None,  # 清空 end_preview
                        "未设置"  # 重置 end_filename
                    )
                    
                except Exception as e:
                    logger.error(f"加载文件夹失败：{e}")
                    return (
                        gr.update(),
                        f"❌ 加载失败：{str(e)}",
                        -1, -1, [], None, "未设置", None, "未设置"
                    )
            
            # 绑定加载文件夹事件
            load_folder_btn.click(
                fn=load_new_folder,
                inputs=[folder_input],
                outputs=[
                    all_images_gallery,
                    status_display,
                    start_index,
                    end_index,
                    current_selection,
                    start_preview,
                    start_filename,
                    end_preview,
                    end_filename
                ]
            )
        
        return self.app
    
    def launch(self, port: int = 7860):
        """启动 Web 界面"""
        import signal
        import sys
        import os
        
        app = self.create_interface()
        
        # 启动服务器
        # 允许访问多个路径：初始目录、/mnt/c 以支持Windows路径、当前项目目录
        allowed_dirs = [
            str(self.input_dir),
            "/mnt/c",  # 允许访问Windows C盘
            "/mnt/d",  # 允许访问Windows D盘（如果有）
            str(Path.cwd()),  # 当前工作目录
            str(Path(__file__).parent.parent.parent)  # 项目根目录
        ]
        
        # 设置信号处理器，用于 Ctrl+C 退出
        def signal_handler(sig, frame):
            logger.info("\n收到退出信号，正在关闭服务器...")
            # 直接强制退出
            os._exit(0)
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        logger.info(f"正在启动 GIF 生成器 GUI...")
        logger.info(f"地址: http://localhost:{port}")
        logger.info("按 Ctrl+C 退出程序")
        
        try:
            # 阻塞式启动（不设置 prevent_thread_lock）
            app.launch(
                server_port=port,
                share=False,
                inbrowser=True,
                quiet=False,
                show_api=False,
                prevent_thread_lock=False,  # 阻塞模式
                max_threads=40,  # 增加最大线程数
                allowed_paths=allowed_dirs  # 允许访问多个目录
            )
        except KeyboardInterrupt:
            logger.info("\n程序已退出")
            sys.exit(0)
        
        return True


def run_gif_maker_gui(input_dir: str, port: int = 7860) -> bool:
    """
    运行 GIF 生成器 GUI
    
    Args:
        input_dir: 输入图片目录
        port: Web 服务器端口
        
    Returns:
        bool: 是否正常退出
    """
    try:
        gui = GifMakerGUI(input_dir)
        
        if not gui.image_files:
            logger.warning(f"在目录 {input_dir} 中未找到数字命名的图片文件，请通过界面加载文件夹")
        else:
            logger.info(f"找到 {len(gui.image_files)} 个图片文件")
        
        logger.info(f"启动 GIF 生成器 GUI，端口：{port}")
        return gui.launch(port=port)
        
    except Exception as e:
        logger.error(f"运行 GUI 失败：{e}")
        return False


# 主程序入口
if __name__ == "__main__":
    import argparse
    from datetime import datetime
    import os
    
    # 创建logs目录
    log_dir = Path(__file__).parent.parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # 设置日志文件名（包含时间戳）
    log_file = log_dir / f"gif_maker_gui_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    # 设置日志 - 同时输出到控制台和文件
    logging.basicConfig(
        level=logging.DEBUG,  # 使用DEBUG级别获取更多信息
        format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        handlers=[
            logging.StreamHandler(),  # 控制台输出
            logging.FileHandler(log_file, encoding='utf-8')  # 文件输出
        ]
    )
    
    logger.info(f"日志文件保存在: {log_file}")
    
    # 解析命令行参数（只保留端口参数）
    parser = argparse.ArgumentParser(description='GIF 生成器 Web GUI')
    parser.add_argument('--port', type=int, default=7860, help='Web 服务器端口（默认：7860）')
    
    args = parser.parse_args()
    
    # 使用当前工作目录作为初始目录（用户可以通过界面更改）
    input_dir = str(Path.cwd())
    logger.info(f"初始目录: {input_dir}")
    logger.info("请通过界面加载图片文件夹")
    
    # 运行 GUI
    run_gif_maker_gui(input_dir, args.port)