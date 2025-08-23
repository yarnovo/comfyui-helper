#!/usr/bin/env python3
"""GIF 动画生成工具模块"""

from pathlib import Path
from PIL import Image
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class GifMaker:
    """GIF 动画生成器"""
    
    def __init__(self):
        """初始化 GIF 生成器"""
        pass
    
    def create_gif(self,
                   image_paths: List[str],
                   output_path: str,
                   duration: int = 100,
                   loop: int = 0,
                   optimize: bool = True,
                   resize_to: Optional[tuple] = None) -> Dict:
        """
        从图片列表创建 GIF 动画
        
        Args:
            image_paths: 图片路径列表（按播放顺序）
            output_path: 输出 GIF 文件路径
            duration: 每帧持续时间（毫秒，默认100ms）
            loop: 循环次数（0表示无限循环）
            optimize: 是否优化GIF大小
            resize_to: 可选的目标尺寸 (width, height)
            
        Returns:
            Dict: 处理结果信息
        """
        result = {
            "success": False,
            "message": "",
            "output_path": "",
            "frame_count": 0,
            "total_duration": 0,
            "file_size": 0,
            "dimensions": (0, 0)
        }
        
        try:
            # 验证输入
            if not image_paths:
                raise ValueError("图片列表不能为空")
            
            # 检查所有输入文件是否存在
            missing_files = []
            for path in image_paths:
                if not Path(path).exists():
                    missing_files.append(path)
            
            if missing_files:
                raise FileNotFoundError(f"以下文件不存在: {', '.join(missing_files[:3])}...")
            
            # 加载所有图片
            images = []
            for i, path in enumerate(image_paths):
                logger.info(f"加载图片 {i+1}/{len(image_paths)}: {Path(path).name}")
                img = Image.open(path)
                
                # 转换为 RGBA 以保持透明度（如果有）
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # 如果指定了目标尺寸，进行缩放
                if resize_to:
                    img = img.resize(resize_to, Image.Resampling.LANCZOS)
                
                images.append(img)
            
            if not images:
                raise ValueError("无法加载任何图片")
            
            # 获取第一张图片的尺寸作为参考
            first_img = images[0]
            dimensions = first_img.size
            
            # 确保所有图片尺寸一致
            for i, img in enumerate(images[1:], 1):
                if img.size != dimensions:
                    logger.warning(f"图片 {image_paths[i]} 尺寸不一致，将调整为 {dimensions}")
                    images[i] = img.resize(dimensions, Image.Resampling.LANCZOS)
            
            # 创建输出目录
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 将 RGBA 转换为调色板模式以减小文件大小
            # GIF 格式不完全支持透明度，需要特殊处理
            processed_images = []
            for img in images:
                # 如果图片有透明度，保留它
                if img.mode == 'RGBA':
                    # 创建一个白色背景
                    background = Image.new('RGBA', img.size, (255, 255, 255, 255))
                    # 将图片粘贴到背景上
                    background.paste(img, mask=img.split()[3] if len(img.split()) > 3 else None)
                    img = background
                
                # 转换为 P 模式（调色板模式）以优化文件大小
                if img.mode != 'P':
                    img = img.convert('P', palette=Image.ADAPTIVE, colors=256)
                
                processed_images.append(img)
            
            # 保存为 GIF
            logger.info(f"生成 GIF 动画: {output_path}")
            processed_images[0].save(
                str(output_path),
                save_all=True,
                append_images=processed_images[1:],
                duration=duration,
                loop=loop,
                optimize=optimize
            )
            
            # 获取文件大小
            file_size = output_path.stat().st_size
            
            # 计算总时长
            total_duration = len(images) * duration
            
            result.update({
                "success": True,
                "message": f"成功生成 GIF 动画，包含 {len(images)} 帧",
                "output_path": str(output_path),
                "frame_count": len(images),
                "total_duration": total_duration,
                "file_size": file_size,
                "dimensions": dimensions
            })
            
            logger.info(f"GIF 生成成功: {output_path} ({len(images)} 帧, {file_size/1024:.1f} KB)")
            
            return result
            
        except Exception as e:
            logger.error(f"生成 GIF 失败: {e}")
            result["message"] = f"生成 GIF 失败: {e}"
            return result
    
    def create_gif_from_directory(self,
                                 input_dir: str,
                                 output_path: str,
                                 pattern: str = "*.png",
                                 duration: int = 100,
                                 loop: int = 0,
                                 optimize: bool = True,
                                 resize_to: Optional[tuple] = None) -> Dict:
        """
        从目录中的图片创建 GIF 动画
        
        Args:
            input_dir: 输入目录路径
            output_path: 输出 GIF 文件路径
            pattern: 文件匹配模式（默认 "*.png"）
            duration: 每帧持续时间（毫秒）
            loop: 循环次数（0表示无限循环）
            optimize: 是否优化GIF大小
            resize_to: 可选的目标尺寸 (width, height)
            
        Returns:
            Dict: 处理结果信息
        """
        try:
            input_path = Path(input_dir)
            if not input_path.exists():
                raise FileNotFoundError(f"输入目录不存在: {input_dir}")
            
            # 查找匹配的文件
            image_files = sorted(input_path.glob(pattern))
            
            if not image_files:
                raise ValueError(f"未找到匹配的图片文件: {pattern}")
            
            # 转换为字符串路径列表
            image_paths = [str(f) for f in image_files]
            
            logger.info(f"从目录 {input_dir} 找到 {len(image_paths)} 个文件")
            
            # 调用主方法创建 GIF
            return self.create_gif(
                image_paths=image_paths,
                output_path=output_path,
                duration=duration,
                loop=loop,
                optimize=optimize,
                resize_to=resize_to
            )
            
        except Exception as e:
            logger.error(f"从目录创建 GIF 失败: {e}")
            return {
                "success": False,
                "message": f"从目录创建 GIF 失败: {e}",
                "output_path": "",
                "frame_count": 0,
                "total_duration": 0,
                "file_size": 0,
                "dimensions": (0, 0)
            }