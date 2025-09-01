"""
背景移除工具模块
使用 RMBG-2.0 模型进行高质量的图像背景移除
"""

import os
import logging
from pathlib import Path
from typing import Union, Optional, Tuple
from PIL import Image
import torch
from torchvision import transforms
from transformers import AutoModelForImageSegmentation

logger = logging.getLogger(__name__)


class BackgroundRemover:
    """使用 RMBG-2.0 模型的背景移除器"""
    
    def __init__(self, device: Optional[str] = None):
        """
        初始化背景移除器
        
        Args:
            device: 设备类型 ('cuda', 'cpu' 或 None 自动检测，默认优先使用 cuda)
        """
        # 默认使用 CUDA，如果不可用才降级到 CPU
        if device is None:
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device
        self.model = None
        self.transform = None
        self.image_size = (1024, 1024)
        
        logger.info(f"初始化背景移除器，设备: {self.device}")
        
    def load_model(self):
        """加载 RMBG-2.0 模型"""
        if self.model is not None:
            return
            
        logger.info("正在加载 RMBG-2.0 模型...")
        
        try:
            # 临时修复：猴子补丁修复 transformers 库的 bug
            from transformers import configuration_utils
            
            # 为 Config 类添加缺失的 is_encoder_decoder 属性
            original_getattr = configuration_utils.PretrainedConfig.__getattribute__
            
            def patched_getattr(self, key):
                try:
                    return original_getattr(self, key)
                except AttributeError:
                    if key == 'is_encoder_decoder':
                        return False  # 默认返回 False，因为 RMBG-2.0 不是编码器-解码器模型
                    raise
            
            configuration_utils.PretrainedConfig.__getattribute__ = patched_getattr
            
            # 加载模型（使用官方方法）
            self.model = AutoModelForImageSegmentation.from_pretrained(
                'briaai/RMBG-2.0',
                trust_remote_code=True
            )
            
            # 恢复原始方法
            configuration_utils.PretrainedConfig.__getattribute__ = original_getattr
            
        except Exception as e:
            logger.error(f"加载模型失败: {e}")
            raise
        
        # 设置精度和设备
        if self.device == 'cuda':
            torch.set_float32_matmul_precision('high')
        
        self.model.to(self.device)
        self.model.eval()
        
        # 设置图像转换
        self.transform = transforms.Compose([
            transforms.Resize(self.image_size),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
        
        logger.info("模型加载完成")
        
    def remove_background(
        self,
        image: Union[str, Path, Image.Image],
        output_path: Optional[Union[str, Path]] = None,
        alpha_matting: bool = True,
        alpha_threshold: int = 0
    ) -> Image.Image:
        """
        移除图像背景
        
        Args:
            image: 输入图像（路径或 PIL Image 对象）
            output_path: 输出路径（可选）
            alpha_matting: 是否使用 alpha 通道（True）或纯白背景（False）
            alpha_threshold: Alpha 阈值（0-255），低于此值的像素将完全透明
            
        Returns:
            处理后的 PIL Image 对象
        """
        # 确保模型已加载
        self.load_model()
        
        # 加载图像
        if isinstance(image, (str, Path)):
            logger.info(f"正在处理图像: {image}")
            input_image = Image.open(image).convert('RGB')
        else:
            input_image = image.convert('RGB')
            
        original_size = input_image.size
        
        # 转换图像
        input_tensor = self.transform(input_image).unsqueeze(0).to(self.device)
        
        # 预测
        logger.info("正在进行背景分割...")
        with torch.no_grad():
            preds = self.model(input_tensor)[-1].sigmoid().cpu()
            
        # 获取预测结果
        pred = preds[0].squeeze()
        pred_pil = transforms.ToPILImage()(pred)
        
        # 调整回原始尺寸
        mask = pred_pil.resize(original_size, Image.Resampling.LANCZOS)
        
        # 应用阈值
        if alpha_threshold > 0:
            import numpy as np
            mask_array = np.array(mask)
            mask_array[mask_array < alpha_threshold] = 0
            mask = Image.fromarray(mask_array)
        
        # 创建输出图像
        if alpha_matting:
            # 使用 alpha 通道
            output_image = input_image.convert('RGBA')
            output_image.putalpha(mask)
        else:
            # 使用白色背景
            output_image = Image.new('RGBA', original_size, (255, 255, 255, 255))
            input_rgba = input_image.convert('RGBA')
            input_rgba.putalpha(mask)
            output_image.paste(input_rgba, (0, 0), input_rgba)
            output_image = output_image.convert('RGB')
            
        # 保存图像
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_image.save(output_path)
            logger.info(f"图像已保存到: {output_path}")
            
        return output_image
        
    def batch_remove_background(
        self,
        input_dir: Union[str, Path],
        output_dir: Union[str, Path],
        extensions: Tuple[str, ...] = ('.png', '.jpg', '.jpeg', '.webp'),
        alpha_matting: bool = True,
        alpha_threshold: int = 0
    ) -> int:
        """
        批量移除图像背景
        
        Args:
            input_dir: 输入目录
            output_dir: 输出目录
            extensions: 支持的图像扩展名
            alpha_matting: 是否使用 alpha 通道
            alpha_threshold: Alpha 阈值
            
        Returns:
            处理的图像数量
        """
        input_dir = Path(input_dir)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 查找所有图像文件
        image_files = []
        for ext in extensions:
            image_files.extend(input_dir.glob(f'*{ext}'))
            image_files.extend(input_dir.glob(f'*{ext.upper()}'))
            
        logger.info(f"找到 {len(image_files)} 个图像文件")
        
        processed = 0
        for image_file in image_files:
            try:
                # 生成输出文件名
                output_name = image_file.stem + '_no_bg.png'
                output_path = output_dir / output_name
                
                # 处理图像
                self.remove_background(
                    image_file,
                    output_path,
                    alpha_matting=alpha_matting,
                    alpha_threshold=alpha_threshold
                )
                
                processed += 1
                logger.info(f"已处理 {processed}/{len(image_files)}: {image_file.name}")
                
            except Exception as e:
                logger.error(f"处理 {image_file} 时出错: {e}")
                
        logger.info(f"批量处理完成，共处理 {processed} 个图像")
        return processed
        
    def clear_cache(self):
        """清理模型缓存"""
        if self.model is not None:
            del self.model
            self.model = None
            
        if self.device == 'cuda':
            torch.cuda.empty_cache()
            
        logger.info("模型缓存已清理")


def remove_background_simple(
    image_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    device: Optional[str] = None
) -> Image.Image:
    """
    简单的背景移除函数
    
    Args:
        image_path: 输入图像路径
        output_path: 输出路径（可选）
        device: 设备类型
        
    Returns:
        处理后的 PIL Image 对象
    """
    remover = BackgroundRemover(device=device)
    return remover.remove_background(image_path, output_path)


if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='RMBG-2.0 背景移除工具')
    parser.add_argument('input', help='输入图像路径')
    parser.add_argument('-o', '--output', help='输出路径（默认: 输入名_no_bg.png）')
    parser.add_argument('-d', '--device', choices=['cuda', 'cpu', 'auto'], default='auto',
                       help='运行设备（默认: auto，自动选择cuda或cpu）')
    parser.add_argument('--white-bg', action='store_true', help='使用白色背景')
    parser.add_argument('--threshold', type=int, default=0, help='Alpha 阈值 (0-255)')
    parser.add_argument('--batch', action='store_true', help='批量处理目录')
    
    args = parser.parse_args()
    
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    device = None if args.device == 'auto' else args.device
    remover = BackgroundRemover(device=device)
    
    try:
        input_path = Path(args.input)
        
        if args.batch or input_path.is_dir():
            # 批量处理
            if not input_path.is_dir():
                logger.error(f"批量模式需要目录，但 {input_path} 不是目录")
                sys.exit(1)
            
            output_dir = Path(args.output) if args.output else input_path.parent / f"{input_path.name}_no_bg"
            processed = remover.batch_remove_background(
                input_path, output_dir,
                alpha_matting=not args.white_bg,
                alpha_threshold=args.threshold
            )
            print(f"✅ 处理完成，共处理 {processed} 个图像")
        else:
            # 单个文件
            if not input_path.exists():
                logger.error(f"文件不存在: {input_path}")
                sys.exit(1)
                
            output_path = Path(args.output) if args.output else input_path.parent / f"{input_path.stem}_no_bg.png"
            remover.remove_background(
                input_path, output_path,
                alpha_matting=not args.white_bg,
                alpha_threshold=args.threshold
            )
            print(f"✅ 处理完成: {output_path}")
            
    except Exception as e:
        logger.error(f"处理失败: {e}")
        sys.exit(1)
    finally:
        remover.clear_cache()