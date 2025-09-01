#!/usr/bin/env python3
"""图片缩放工具模块"""

from pathlib import Path
from PIL import Image
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class ImageScaler:
    """图片缩放器"""
    
    # 支持的图片格式
    SUPPORTED_FORMATS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp'}
    
    # 重采样算法映射
    RESAMPLING_FILTERS = {
        'nearest': Image.Resampling.NEAREST,      # 最近邻，适合像素艺术
        'bilinear': Image.Resampling.BILINEAR,    # 双线性
        'bicubic': Image.Resampling.BICUBIC,      # 双三次
        'lanczos': Image.Resampling.LANCZOS,      # Lanczos，高质量
        'box': Image.Resampling.BOX,              # 箱式滤波
        'hamming': Image.Resampling.HAMMING       # Hamming窗口
    }
    
    def __init__(self):
        """初始化图片缩放器"""
        pass
    
    def scale_image(self, 
                   input_path: str,
                   output_path: Optional[str] = None,
                   scale_factor: Optional[float] = None,
                   target_width: Optional[int] = None,
                   target_height: Optional[int] = None,
                   keep_aspect_ratio: bool = True,
                   resampling: str = 'lanczos',
                   quality: int = 95) -> Dict:
        """
        缩放单张图片
        
        Args:
            input_path: 输入图片路径
            output_path: 输出图片路径，如果为None则自动生成
            scale_factor: 缩放倍数（如0.5表示缩小一半，2表示放大一倍）
            target_width: 目标宽度（像素）
            target_height: 目标高度（像素）
            keep_aspect_ratio: 是否保持宽高比
            resampling: 重采样算法 ('nearest', 'bilinear', 'bicubic', 'lanczos', 'box', 'hamming')
            quality: JPEG质量（1-100，仅对JPEG格式有效）
            
        Returns:
            Dict: 处理结果信息
        """
        result = {
            "success": False,
            "message": "",
            "input_path": input_path,
            "output_path": "",
            "original_size": (0, 0),
            "new_size": (0, 0),
            "scale_factor": 0
        }
        
        try:
            # 验证输入文件
            input_file = Path(input_path)
            if not input_file.exists():
                raise FileNotFoundError(f"输入文件不存在: {input_path}")
            
            if input_file.suffix.lower() not in self.SUPPORTED_FORMATS:
                raise ValueError(f"不支持的图片格式: {input_file.suffix}")
            
            # 打开图片
            img = Image.open(input_path)
            original_width, original_height = img.size
            result["original_size"] = (original_width, original_height)
            
            # 计算目标尺寸
            new_width, new_height = self._calculate_target_size(
                original_width, original_height,
                scale_factor, target_width, target_height,
                keep_aspect_ratio
            )
            
            # 验证参数组合
            if new_width <= 0 or new_height <= 0:
                raise ValueError("目标尺寸必须大于0")
            
            # 获取重采样算法
            if resampling not in self.RESAMPLING_FILTERS:
                logger.warning(f"未知的重采样算法 {resampling}，使用默认 lanczos")
                resampling = 'lanczos'
            resample_filter = self.RESAMPLING_FILTERS[resampling]
            
            # 缩放图片
            logger.info(f"缩放图片: {original_width}x{original_height} -> {new_width}x{new_height}")
            scaled_img = img.resize((new_width, new_height), resample_filter)
            
            # 生成输出路径
            if output_path is None:
                output_path = self._generate_output_path(input_path, new_width, new_height)
            
            # 确保输出目录存在
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存图片
            save_kwargs = {}
            if output_file.suffix.lower() in ['.jpg', '.jpeg']:
                save_kwargs['quality'] = quality
                save_kwargs['optimize'] = True
            elif output_file.suffix.lower() == '.png':
                save_kwargs['optimize'] = True
                
            scaled_img.save(output_path, **save_kwargs)
            
            # 计算实际缩放比例
            actual_scale = (new_width / original_width + new_height / original_height) / 2
            
            result.update({
                "success": True,
                "message": f"图片缩放成功: {new_width}x{new_height}",
                "output_path": str(output_path),
                "new_size": (new_width, new_height),
                "scale_factor": actual_scale
            })
            
            return result
            
        except Exception as e:
            logger.error(f"图片缩放失败: {e}")
            result["message"] = f"图片缩放失败: {e}"
            return result
    
    def _calculate_target_size(self,
                              original_width: int,
                              original_height: int,
                              scale_factor: Optional[float],
                              target_width: Optional[int],
                              target_height: Optional[int],
                              keep_aspect_ratio: bool) -> Tuple[int, int]:
        """
        计算目标尺寸
        
        优先级：
        1. scale_factor（缩放倍数）
        2. target_width 和 target_height
        3. 只有 target_width 或 target_height（保持比例）
        """
        # 使用缩放倍数
        if scale_factor is not None:
            new_width = int(original_width * scale_factor)
            new_height = int(original_height * scale_factor)
            return new_width, new_height
        
        # 指定了宽高
        if target_width is not None and target_height is not None:
            if keep_aspect_ratio:
                # 计算缩放比例，选择较小的
                scale_w = target_width / original_width
                scale_h = target_height / original_height
                scale = min(scale_w, scale_h)
                new_width = int(original_width * scale)
                new_height = int(original_height * scale)
            else:
                new_width = target_width
                new_height = target_height
            return new_width, new_height
        
        # 只指定宽度
        if target_width is not None:
            scale = target_width / original_width
            new_width = target_width
            new_height = int(original_height * scale) if keep_aspect_ratio else original_height
            return new_width, new_height
        
        # 只指定高度
        if target_height is not None:
            scale = target_height / original_height
            new_width = int(original_width * scale) if keep_aspect_ratio else original_width
            new_height = target_height
            return new_width, new_height
        
        # 没有指定任何参数，返回原尺寸
        raise ValueError("必须指定 scale_factor、target_width 或 target_height 至少一个参数")
    
    def _generate_output_path(self, input_path: str, width: int, height: int) -> str:
        """生成输出文件路径"""
        input_file = Path(input_path)
        stem = input_file.stem
        suffix = input_file.suffix
        parent = input_file.parent
        
        output_name = f"{stem}_{width}x{height}{suffix}"
        return str(parent / output_name)