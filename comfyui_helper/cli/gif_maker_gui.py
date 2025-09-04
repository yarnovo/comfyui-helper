#!/usr/bin/env python3
"""带 Web GUI 的视频转 GIF 动画工具"""

import os
# 设置环境变量去除代理，确保 localhost 可访问
os.environ['NO_PROXY'] = 'localhost,127.0.0.1'
os.environ['no_proxy'] = 'localhost,127.0.0.1'

import gradio as gr
from pathlib import Path
from typing import List, Optional, Tuple
import logging
import json
from datetime import datetime
import sys
import tempfile
import shutil

# 支持直接运行
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from comfyui_helper.core.gif_maker import GifMaker
    from comfyui_helper.core.video_frame_extractor import VideoFrameExtractor
    from comfyui_helper.core.background_remover import BackgroundRemover
else:
    from ..core.gif_maker import GifMaker
    from ..core.video_frame_extractor import VideoFrameExtractor
    from ..core.background_remover import BackgroundRemover

logger = logging.getLogger(__name__)


class GifMakerGUI:
    """GIF 生成器 Web GUI"""
    
    def __init__(self):
        """
        初始化 GUI
        """
        self.gif_maker = GifMaker()
        try:
            self.video_extractor = VideoFrameExtractor()
        except RuntimeError as e:
            logger.warning(f"视频提取器初始化失败: {e}，视频功能将不可用")
            self.video_extractor = None
        self.background_remover = None  # 延迟加载背景移除器
        self.image_files = []
        self.should_exit = False
        self.app = None
        self.current_gif_data = None  # 存储当前生成的 GIF 数据
        self.current_gif_config = None  # 存储当前 GIF 配置
        self.temp_frames = []  # 保存临时帧文件路径
    
    
    def get_video_info_preview(self, video_file) -> str:
        """获取视频信息用于预览"""
        if not video_file:
            return ""
        
        if not self.video_extractor:
            return "⚠️ 视频功能不可用（需要安装 ffmpeg）"
        
        try:
            video_info = self.video_extractor.get_video_info(video_file)
            info = f"""📹 视频信息：
时长: {video_info['duration']:.1f} 秒
FPS: {video_info['fps']:.1f}
分辨率: {video_info['width']}x{video_info['height']}
总帧数: {video_info['total_frames']}
编码: {video_info['codec']}"""
            return info
        except Exception as e:
            return f"⚠️ 无法获取视频信息: {str(e)}"
    
    def process_video(self, video_file, fps: float = 10, progress=gr.Progress()) -> Tuple[List, str, List]:
        """处理上传的视频文件，提取帧到内存"""
        if not video_file:
            return None, "请先上传视频文件", []
        
        if not self.video_extractor:
            return None, "❌ 视频功能不可用（需要安装 ffmpeg）", []
        
        try:
            progress(0, desc="正在处理视频...")
            
            # 清理之前的临时帧
            self._cleanup_temp_frames()
            
            # 创建临时目录
            temp_dir = tempfile.mkdtemp(prefix="gif_frames_")
            
            progress(0.2, desc="正在提取视频帧...")
            
            # 提取视频帧
            result = self.video_extractor.extract_frames(
                video_path=video_file,
                output_dir=temp_dir,
                fps=fps,  # 每秒提取的帧数
                output_format="png",
                output_prefix="frame"
            )
            
            # 检查是否成功
            if not result.get("success", False):
                return None, f"❌ 视频处理失败: {result.get('message', '未知错误')}", []
            
            progress(0.6, desc="正在加载帧图片...")
            
            # 获取所有提取的帧
            frame_files = sorted(
                Path(temp_dir).glob("frame_*.png"),
                key=lambda x: int(x.stem.split('_')[1])
            )
            
            self.temp_frames = [str(f) for f in frame_files]
            self.image_files = self.temp_frames.copy()
            
            # 准备显示的图片数据
            display_images = [(str(f), Path(f).name) for f in frame_files]
            
            progress(1.0, desc="完成！")
            
            info = f"""✅ 视频处理成功！
提取了 {result['frame_count']} 帧
视频时长: {result['video_info']['duration']:.1f} 秒
原始FPS: {result['video_info']['fps']:.1f}
提取FPS: {fps}
视频尺寸: {result['video_info']['width']}x{result['video_info']['height']}

现在可以选择要使用的帧范围来生成 GIF"""
            
            return display_images, info, self.image_files
            
        except Exception as e:
            logger.error(f"处理视频失败: {e}")
            return None, f"❌ 处理视频失败: {str(e)}", []
    
    def _cleanup_temp_frames(self):
        """清理临时帧文件"""
        if self.temp_frames:
            for frame_path in self.temp_frames:
                try:
                    if Path(frame_path).exists():
                        Path(frame_path).unlink()
                except Exception as e:
                    logger.warning(f"清理临时文件失败: {e}")
            
            # 清理临时目录
            if self.temp_frames:
                temp_dir = Path(self.temp_frames[0]).parent
                try:
                    if temp_dir.exists() and temp_dir.name.startswith("gif_frames_"):
                        temp_dir.rmdir()
                except Exception as e:
                    logger.warning(f"清理临时目录失败: {e}")
            
            self.temp_frames = []
    
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
    
    def export_frames(self, output_dir: str = None, remove_bg: bool = True, progress=gr.Progress()) -> str:
        """导出 GIF 的帧图片到指定目录"""
        if not self.current_gif_config or 'selected_files' not in self.current_gif_config:
            return "❌ 没有可导出的帧，请先生成 GIF 预览"
        
        try:
            # 使用提供的路径或默认路径
            if not output_dir or output_dir.strip() == "":
                output_dir = "/mnt/c/Users/yarnb/Desktop"
            
            # 创建输出目录
            export_path = Path(output_dir)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            frames_dir = export_path / f"gif_frames_{timestamp}"
            frames_dir.mkdir(parents=True, exist_ok=True)
            
            # 获取选中的文件列表
            selected_files = self.current_gif_config.get('selected_files', [])
            if not selected_files:
                return "❌ 没有选中的帧图片"
            
            # 如果需要去除背景，初始化背景移除器
            if remove_bg:
                if self.background_remover is None:
                    progress(0, desc="正在初始化背景移除模型...")
                    logger.info("初始化背景移除器...")
                    try:
                        self.background_remover = BackgroundRemover()
                        self.background_remover.load_model()
                        logger.info("背景移除器初始化成功")
                    except Exception as e:
                        logger.error(f"初始化背景移除器失败: {e}")
                        return f"❌ 初始化背景移除器失败：{str(e)}"
            
            # 处理并导出帧图片
            exported_count = 0
            total_files = len(selected_files)
            
            for i, src_path in enumerate(selected_files):
                src = Path(src_path)
                if src.exists():
                    # 更新进度
                    if remove_bg:
                        progress((i / total_files) * 0.9, desc=f"正在处理第 {i+1}/{total_files} 帧...")
                    else:
                        progress(i / total_files, desc=f"正在导出第 {i+1}/{total_files} 帧...")
                    
                    # 生成新的文件名（保持顺序）
                    dst_name = f"frame_{i:04d}.png"  # 始终使用PNG格式（支持透明背景）
                    dst = frames_dir / dst_name
                    
                    if remove_bg:
                        # 去除背景
                        try:
                            # 调用 remove_background 方法
                            processed_image = self.background_remover.remove_background(
                                image=str(src),
                                output_path=str(dst),
                                alpha_matting=True,  # 使用透明背景
                                alpha_threshold=0
                            )
                            exported_count += 1
                        except Exception as e:
                            logger.error(f"处理图片 {src_path} 失败: {e}")
                            # 如果处理失败，直接复制原图
                            shutil.copy2(src, dst)
                            exported_count += 1
                    else:
                        # 直接复制文件
                        shutil.copy2(src, dst)
                        exported_count += 1
            
            progress(1.0, desc="完成！")
            
            result_msg = f"""✅ 帧图片导出成功！
            
导出目录：{frames_dir}
帧数量：{exported_count}
背景处理：{'已去除背景（透明PNG）' if remove_bg else '保留原始背景'}

提示：你可以使用这些帧图片在其他软件中制作动画"""
            
            return result_msg
            
        except Exception as e:
            logger.error(f"导出帧图片失败：{e}")
            return f"❌ 导出失败：{str(e)}"
    
    def save_gif(self, output_dir: str = None) -> str:
        """保存当前的 GIF 到指定目录"""
        if not self.current_gif_data:
            return "❌ 没有可保存的 GIF，请先生成预览"
        
        try:
            # 使用提供的路径或默认路径
            if not output_dir or output_dir.strip() == "":
                save_dir = Path("/mnt/c/Users/yarnb/Desktop/my_frames")
            else:
                save_dir = Path(output_dir)
            
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
        with gr.Blocks(title="视频转GIF生成器", theme=gr.themes.Soft()) as self.app:
            gr.Markdown("# 🎬 视频转 GIF 生成器")
            
            # 存储当前选择的状态
            start_index = gr.State(-1)
            end_index = gr.State(-1)
            current_selection = gr.State([])
            
            # 视频转GIF界面
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 上传视频文件")
                    video_input = gr.File(
                        label="选择视频文件",
                        file_types=[".mp4", ".avi", ".mov", ".mkv", ".webm"],
                        type="filepath"
                    )
                    
                    # 视频预览
                    video_preview = gr.Video(
                        label="视频预览",
                        height=200,
                        interactive=False,
                        autoplay=False
                    )
                    
                    fps_slider = gr.Slider(
                        minimum=1,
                        maximum=30,
                        value=10,
                        step=1,
                        label="提取帧率 (FPS)",
                        info="每秒提取多少帧"
                    )
                    
                    process_video_btn = gr.Button("🎞️ 处理视频", variant="primary")
                    video_info = gr.Textbox(label="处理结果", lines=6)
                
                with gr.Column(scale=2):
                    gr.Markdown("### 提取的帧")
                    video_frames_gallery = gr.Gallery(
                        label="视频帧（点击选择开始和结束）",
                        columns=4,
                        rows=3,
                        height=400,
                        interactive=True,
                        type="filepath"
                    )
            
            with gr.Row():
                # 左侧：帧选择
                with gr.Column(scale=1):
                    gr.Markdown("### 🎯 选择帧范围")
                    
                    # 设置按钮
                    with gr.Row():
                        set_start_btn = gr.Button("📍 设为开始", variant="primary", scale=1)
                        set_end_btn = gr.Button("🎯 设为结束", variant="primary", scale=1)
                    
                    # 显示当前选择（图片预览和文件名）
                    with gr.Row():
                        with gr.Column(scale=1):
                            start_preview = gr.Image(label="开始帧", height=100, interactive=False)
                            start_filename = gr.Textbox(label="文件名", value="未设置", interactive=False)
                        with gr.Column(scale=1):
                            end_preview = gr.Image(label="结束帧", height=100, interactive=False)
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
                    
                    # 导出选项
                    gr.Markdown("### 💾 导出选项")
                    
                    with gr.Row():
                        # 导出路径输入
                        export_path_input = gr.Textbox(
                            label="导出路径",
                            value="/mnt/c/Users/yarnb/Desktop",
                            info="可修改为其他路径"
                        )
                    
                    # 去除背景复选框
                    remove_bg_checkbox = gr.Checkbox(
                        label="🎨 去除背景（透明PNG）",
                        value=True,
                        info="导出时自动去除背景，生成透明PNG图片"
                    )
                    
                    # 导出帧按钮
                    export_frames_btn = gr.Button("📁 导出帧图片", variant="primary", size="lg")
                    
                    # 操作结果显示
                    operation_result = gr.Textbox(
                        label="操作结果",
                        lines=4,
                        interactive=False
                    )
            
            # 事件绑定（简化版）
            
            # 存储当前选中的图片索引
            current_selected_index = gr.State(-1)
            
            # 存储当前显示的所有图片路径
            displayed_images = gr.State([])
            
            # Gallery 选择事件 - 现在可以自定义处理逻辑
            def on_gallery_select(evt: gr.SelectData, _current_images):
                """Gallery选择事件的主处理器"""
                # 这里可以添加自定义逻辑
                # 例如：记录选择历史、验证选择、触发其他操作等
                
                if evt:
                    logger.debug(f"Gallery选择事件: index={evt.index}")
                    # 可以在这里添加更多自定义处理
                    # 例如：检查图片是否有效、预加载相关数据等
                    return evt.index
                return -1
            
            # Gallery 更新时同步更新内部文件列表
            def on_gallery_update(gallery_value):
                """当Gallery内容更新时，同步更新内部文件列表"""
                if gallery_value:
                    # Gallery可能返回不同格式：
                    # 1. 字符串列表 ['path1', 'path2']
                    # 2. 元组列表 [('path1', 'label1'), ('path2', 'label2')]
                    processed_files = []
                    for item in gallery_value:
                        if isinstance(item, tuple):
                            # 如果是元组，取第一个元素（文件路径）
                            processed_files.append(item[0])
                        else:
                            # 如果是字符串，直接使用
                            processed_files.append(item)
                    
                    self.image_files = processed_files
                    logger.debug(f"Gallery更新，新文件数量: {len(self.image_files)}, 类型: {type(gallery_value[0]) if gallery_value else None}")
                    return processed_files
                return []
            
            
            # 设为开始帧 - 使用当前显示的图片列表
            def set_start(idx, current_images):
                if current_images and idx >= 0 and idx < len(current_images):
                    item = current_images[idx]
                    # 处理可能的元组格式
                    if isinstance(item, tuple):
                        file_path = item[0]  # 元组的第一个元素是文件路径
                    else:
                        file_path = item
                    
                    file_name = Path(file_path).name
                    logger.debug(f"设为开始帧: idx={idx}, path={file_path}, type={type(item)}")
                    return idx, file_path, file_name  # 返回索引、图片路径和文件名
                logger.debug(f"设为开始帧失败: idx={idx}, images_count={len(current_images) if current_images else 0}")
                return -1, None, "未设置"  # 返回默认值
            
            # 设为结束帧 - 使用当前显示的图片列表
            def set_end(idx, current_images):
                if current_images and idx >= 0 and idx < len(current_images):
                    item = current_images[idx]
                    # 处理可能的元组格式
                    if isinstance(item, tuple):
                        file_path = item[0]  # 元组的第一个元素是文件路径
                    else:
                        file_path = item
                    
                    file_name = Path(file_path).name
                    logger.debug(f"设为结束帧: idx={idx}, path={file_path}, type={type(item)}")
                    return idx, file_path, file_name  # 返回索引、图片路径和文件名
                logger.debug(f"设为结束帧失败: idx={idx}, images_count={len(current_images) if current_images else 0}")
                return -1, None, "未设置"  # 返回默认值
            
            # 更新选择范围（返回选中的文件列表）- 使用当前显示的图片列表
            def update_range(start_idx, end_idx, current_images):
                if current_images and start_idx >= 0 and end_idx >= 0:
                    if start_idx > end_idx:
                        start_idx, end_idx = end_idx, start_idx
                    
                    # 处理可能的元组格式
                    selected = []
                    for i in range(start_idx, end_idx + 1):
                        if i < len(current_images):
                            item = current_images[i]
                            if isinstance(item, tuple):
                                selected.append(item[0])  # 元组的第一个元素是文件路径
                            else:
                                selected.append(item)
                    
                    logger.debug(f"更新选择范围: {start_idx} 到 {end_idx}, 共 {len(selected)} 个文件")
                    return selected
                return []
            
            # 点击设为开始 - 添加displayed_images作为输入
            set_start_btn.click(
                fn=set_start,
                inputs=[current_selected_index, displayed_images],
                outputs=[start_index, start_preview, start_filename]  # 输出索引、图片和文件名
            ).then(
                fn=update_range,
                inputs=[start_index, end_index, displayed_images],
                outputs=[current_selection]  # 只输出当前选择的文件列表
            )
            
            # 点击设为结束 - 添加displayed_images作为输入
            set_end_btn.click(
                fn=set_end,
                inputs=[current_selected_index, displayed_images],
                outputs=[end_index, end_preview, end_filename]  # 输出索引、图片和文件名
            ).then(
                fn=update_range,
                inputs=[start_index, end_index, displayed_images],
                outputs=[current_selection]  # 只输出当前选择的文件列表
            )
            
            # 生成 GIF（修改为同时保存配置）
            def generate_and_preview(selected_files, duration):
                """生成 GIF 并保存配置供导出使用"""
                if not selected_files:
                    return None, "请先选择图片"
                
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
                            # 保存配置信息供后续导出使用
                            self.current_gif_config = {
                                "created_at": datetime.now().isoformat(),
                                "frame_count": result["frame_count"],
                                "duration_per_frame": duration,
                                "total_duration_ms": result["total_duration"],
                                "loop": 0,
                                "optimize": True,
                                "dimensions": {
                                    "width": result["dimensions"][0],
                                    "height": result["dimensions"][1]
                                },
                                "file_size_bytes": result["file_size"],
                                "selected_files": selected_files  # 保存选中的文件列表
                            }
                            
                            # 读取 GIF 数据到内存
                            with open(tmp.name, 'rb') as f:
                                self.current_gif_data = f.read()
                            
                            info = f"✅ GIF 生成成功！帧数: {result['frame_count']}, 大小: {result['file_size']/1024:.1f}KB"
                            return tmp.name, info
                        else:
                            return None, f"❌ 生成失败: {result.get('message', '未知错误')}"
                except Exception as e:
                    logger.error(f"生成 GIF 失败：{e}")
                    return None, f"❌ 生成失败: {str(e)}"
            
            # 生成 GIF
            preview_gif_btn.click(
                fn=generate_and_preview,
                inputs=[current_selection, duration],
                outputs=[gif_output, operation_result]
            )
            
            # 导出帧图片
            export_frames_btn.click(
                fn=self.export_frames,
                inputs=[export_path_input, remove_bg_checkbox],
                outputs=[operation_result]
            )
            
            # 视频上传时自动预览和显示信息
            def on_video_upload(video):
                if video:
                    info = self.get_video_info_preview(video)
                    return video, info
                return None, ""
            
            video_input.change(
                fn=on_video_upload,
                inputs=[video_input],
                outputs=[video_preview, video_info]
            )
            
            # 视频处理事件
            process_video_btn.click(
                fn=self.process_video,
                inputs=[video_input, fps_slider],
                outputs=[video_frames_gallery, video_info, displayed_images]
            )
            
            # 视频帧选择事件（共用相同的选择逻辑）
            video_frames_gallery.select(
                fn=on_gallery_select,
                inputs=[displayed_images],
                outputs=[current_selected_index]
            )
            
            # 当视频Gallery文件改变时更新displayed_images
            video_frames_gallery.change(
                fn=on_gallery_update,
                inputs=[video_frames_gallery],
                outputs=[displayed_images]
            )
            
        
        return self.app
    
    def launch(self, port: int = 7860):
        """启动 Web 界面"""
        import signal
        import sys
        
        app = self.create_interface()
        
        # 启动服务器
        # 允许访问多个路径：/mnt/c 以支持Windows路径、当前项目目录
        allowed_dirs = [
            "/mnt/c",  # 允许访问Windows C盘
            "/mnt/d",  # 允许访问Windows D盘（如果有）
            str(Path.cwd()),  # 当前工作目录
            str(Path(__file__).parent.parent.parent)  # 项目根目录
        ]
        
        # 设置信号处理器，用于 Ctrl+C 退出
        def signal_handler(*_args):
            logger.info("\n收到退出信号，正在关闭服务器...")
            # 直接强制退出
            sys.exit(0)
            
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


def run_gif_maker_gui(port: int = 7860) -> bool:
    """
    运行 GIF 生成器 GUI
    
    Args:
        port: Web 服务器端口
        
    Returns:
        bool: 是否正常退出
    """
    try:
        gui = GifMakerGUI()
        
        logger.info(f"启动视频转GIF生成器 GUI，端口：{port}")
        return gui.launch(port=port)
        
    except Exception as e:
        logger.error(f"运行 GUI 失败：{e}")
        return False


def main():
    """主函数入口"""
    import argparse
    from datetime import datetime
    
    # 创建logs目录（在项目根目录下）
    log_dir = Path(__file__).parent.parent.parent.parent / "logs"
    log_dir.mkdir(exist_ok=True, parents=True)
    
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
    parser = argparse.ArgumentParser(description='视频转GIF生成器 Web GUI')
    parser.add_argument('--port', type=int, default=7860, help='Web 服务器端口（默认：7860）')
    
    args = parser.parse_args()
    
    logger.info("请通过界面上传视频文件")
    
    # 运行 GUI
    run_gif_maker_gui(args.port)


# 主程序入口
if __name__ == "__main__":
    main()