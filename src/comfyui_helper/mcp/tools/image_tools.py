"""
图像处理相关的 MCP 工具
"""

import logging
from pathlib import Path
from ...core.image_scaler import ImageScaler
from ...core.background_remover import BackgroundRemover

logger = logging.getLogger(__name__)


def register_image_tools(mcp):
    """注册图像处理相关的 MCP 工具"""
    
    @mcp.tool()
    def scale_image(
        input_path: str,
        output_path: str = None,
        scale_factor: float = None,
        target_width: int = None,
        target_height: int = None,
        keep_aspect_ratio: bool = True,
        resampling: str = 'lanczos',
        quality: int = 95
    ) -> str:
        """
        缩放单张图片
        
        Args:
            input_path: 输入图片路径
            output_path: 输出图片路径（可选，默认在同目录生成 {原名}_{宽}x{高}.{扩展名}）
            scale_factor: 缩放倍数（如0.5=缩小一半，2=放大一倍）
            target_width: 目标宽度（像素）
            target_height: 目标高度（像素）
            keep_aspect_ratio: 是否保持宽高比
            resampling: 重采样算法（nearest适合像素艺术/bilinear/bicubic/lanczos适合照片）
            quality: JPEG质量（1-100，仅对JPEG有效）
            
        Returns:
            处理结果信息
        """
        try:
            scaler = ImageScaler()
            
            # 缩放图片
            result = scaler.scale_image(
                input_path=input_path,
                output_path=output_path,
                scale_factor=scale_factor,
                target_width=target_width,
                target_height=target_height,
                keep_aspect_ratio=keep_aspect_ratio,
                resampling=resampling,
                quality=quality
            )
            
            if result['success']:
                response_text = f"""✅ 图片缩放成功！

原始图片:
- 路径: {result['input_path']}
- 尺寸: {result['original_width']}x{result['original_height']}
- 格式: {result['format']}

输出图片:
- 路径: {result['output_path']}
- 尺寸: {result['new_width']}x{result['new_height']}
- 缩放比例: {result['actual_scale_factor']:.2f}x
- 重采样算法: {result['resampling']}"""
                
                if result['format'] == 'JPEG':
                    response_text += f"\n- JPEG质量: {result['quality']}"
                    
                return response_text
            else:
                return f"❌ {result['message']}"
                
        except Exception as e:
            logger.error(f"图片缩放失败: {e}")
            return f"❌ 缩放失败: {str(e)}"
    
    @mcp.tool()
    def remove_background(
        input_path: str,
        output_path: str = None,
        use_white_bg: bool = False,
        alpha_threshold: int = 0
    ) -> str:
        """
        使用 RMBG-2.0 模型移除图像背景
        
        Args:
            input_path: 输入图像路径
            output_path: 输出路径（可选，默认在同目录生成 {原名}_no_bg.png）
            use_white_bg: 是否使用白色背景（False=透明背景，True=白色背景）
            alpha_threshold: Alpha 阈值（0-255），低于此值的像素将完全透明
            
        Returns:
            处理结果信息
        """
        try:
            from pathlib import Path
            
            # 创建背景移除器（自动选择最佳设备）
            remover = BackgroundRemover()
            
            # 处理输入路径
            input_file = Path(input_path)
            if not input_file.exists():
                return f"❌ 错误：输入文件不存在: {input_path}"
            
            # 设置输出路径
            if output_path is None:
                output_path = input_file.parent / f"{input_file.stem}_no_bg.png"
            else:
                output_path = Path(output_path)
                
            # 移除背景
            result_image = remover.remove_background(
                image=input_file,
                output_path=output_path,
                alpha_matting=not use_white_bg,
                alpha_threshold=alpha_threshold
            )
            
            # 清理缓存
            remover.clear_cache()
            
            response_text = f"""✅ 背景移除成功！

图像信息:
- 输入文件: {input_path}
- 输出文件: {output_path}
- 背景类型: {'白色背景' if use_white_bg else '透明背景'}
- Alpha 阈值: {alpha_threshold}
- 使用设备: {remover.device.upper()}
- 图像尺寸: {result_image.size[0]}x{result_image.size[1]}"""
            
            return response_text
            
        except Exception as e:
            logger.error(f"背景移除失败: {e}")
            return f"❌ 错误: {str(e)}"
    
    @mcp.tool()
    def batch_remove_background(
        input_dir: str,
        output_dir: str = None,
        use_white_bg: bool = False,
        alpha_threshold: int = 0,
        extensions: list = None
    ) -> str:
        """
        批量移除多个图像的背景
        
        Args:
            input_dir: 输入目录路径
            output_dir: 输出目录路径（可选，默认在输入目录创建 {目录名}_no_bg/）
            use_white_bg: 是否使用白色背景（False=透明背景，True=白色背景）
            alpha_threshold: Alpha 阈值（0-255），低于此值的像素将完全透明
            extensions: 支持的文件扩展名列表（默认: ['.png', '.jpg', '.jpeg', '.webp']）
            
        Returns:
            处理结果信息
        """
        try:
            from pathlib import Path
            
            # 创建背景移除器（自动选择最佳设备）
            remover = BackgroundRemover()
            
            # 处理路径
            input_path = Path(input_dir)
            if not input_path.exists() or not input_path.is_dir():
                return f"❌ 错误：输入目录不存在或不是目录: {input_dir}"
            
            # 设置输出目录
            if output_dir is None:
                output_path = input_path.parent / f"{input_path.name}_no_bg"
            else:
                output_path = Path(output_dir)
                
            # 设置扩展名
            if extensions is None:
                extensions = ['.png', '.jpg', '.jpeg', '.webp']
            
            # 批量处理
            processed = remover.batch_remove_background(
                input_dir=input_path,
                output_dir=output_path,
                extensions=tuple(extensions),
                alpha_matting=not use_white_bg,
                alpha_threshold=alpha_threshold
            )
            
            # 清理缓存
            remover.clear_cache()
            
            response_text = f"""✅ 批量背景移除完成！

处理信息:
- 输入目录: {input_dir}
- 输出目录: {output_path}
- 处理文件数: {processed}
- 背景类型: {'白色背景' if use_white_bg else '透明背景'}
- Alpha 阈值: {alpha_threshold}
- 使用设备: {remover.device.upper()}
- 支持格式: {', '.join(extensions)}"""
            
            return response_text
            
        except Exception as e:
            logger.error(f"批量背景移除失败: {e}")
            return f"❌ 错误: {str(e)}"