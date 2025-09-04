#!/usr/bin/env python3
"""HD2D 精灵表拼接工具模块"""

import os
import json
from pathlib import Path
from PIL import Image
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class SpriteSheetComposer:
    """精灵表拼接器"""
    
    def __init__(self, config: Dict):
        """
        初始化精灵表拼接器
        
        Args:
            config: 配置字典，必须提供
        
        Raises:
            ValueError: 如果配置为空或缺少必要字段
        """
        if not config:
            raise ValueError("必须提供配置字典")
        
        # 验证必要的配置字段
        required_fields = ['frame_width', 'frame_height', 'cols', 'rows', 'animations']
        missing_fields = [field for field in required_fields if field not in config]
        if missing_fields:
            raise ValueError(f"配置缺少必要字段: {', '.join(missing_fields)}")
        
        self.config = config
        self.frame_width = config['frame_width']
        self.frame_height = config['frame_height']
        self.cols = config['cols']
        self.rows = config['rows']
        self.animations = config['animations']
        self.background_color = tuple(config.get('background_color', [0, 0, 0, 0]))
    
    
    @staticmethod
    def load_config_file(config_path: str) -> Dict:
        """从文件加载配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            Dict: 配置字典
            
        Raises:
            FileNotFoundError: 如果配置文件不存在
            json.JSONDecodeError: 如果配置文件格式错误
            ValueError: 如果配置缺少必要字段
        """
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                logger.info(f"已加载配置文件: {config_path}")
                
                # 验证必要的配置字段
                required_fields = ['frame_width', 'frame_height', 'cols', 'rows', 'animations']
                missing_fields = [field for field in required_fields if field not in config]
                if missing_fields:
                    raise ValueError(f"配置文件缺少必要字段: {', '.join(missing_fields)}")
                
                return config
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"配置文件格式错误: {config_path}", e.doc, e.pos)
        except Exception as e:
            raise Exception(f"加载配置文件失败: {e}")
    
    def find_frames(self, input_dir: str) -> Dict[str, List[str]]:
        """
        扫描输入目录，按动画类型分组找到所有帧文件
        目录结构：animation_name/001.png
        
        Args:
            input_dir: 输入目录路径
            
        Returns:
            Dict[动画名称, 帧文件路径列表]
        """
        input_path = Path(input_dir)
        if not input_path.exists():
            raise FileNotFoundError(f"输入目录不存在: {input_dir}")
        
        found_frames = {}
        
        # 遍历所有子目录
        for subdir in input_path.iterdir():
            if subdir.is_dir():
                anim_name = subdir.name
                frame_files = []
                
                # 查找子目录中的所有PNG文件
                for file_path in subdir.glob("*.png"):
                    filename = file_path.stem
                    try:
                        # 将文件名解析为数字（如 001, 002）
                        frame_num = int(filename)
                        frame_files.append((frame_num, str(file_path)))
                    except ValueError:
                        logger.warning(f"无法解析帧序号: {file_path}")
                
                if frame_files:
                    frame_files.sort(key=lambda x: x[0])
                    found_frames[anim_name] = [path for _, path in frame_files]
                    logger.info(f"在子目录 {anim_name} 中找到 {len(frame_files)} 帧")
        
        if not found_frames:
            logger.warning("未找到任何动画帧。请确保目录结构为: animation_name/001.png")
        
        return found_frames
    
    def create_sprite_sheet(self, input_dir: str, output_path: str) -> Dict:
        """
        创建精灵表
        
        Args:
            input_dir: 输入图片目录
            output_path: 输出精灵表路径
            
        Returns:
            Dict: 包含结果信息的字典
        """
        result = {
            "success": False,
            "message": "",
            "output_path": "",
            "config_path": "",
            "processed_frames": 0,
            "missing_frames": 0,
            "sheet_width": 0,
            "sheet_height": 0
        }
        
        try:
            logger.info("开始创建精灵表...")
            
            found_frames = self.find_frames(input_dir)
            logger.info(f"找到 {len(found_frames)} 种动画类型")
            
            sheet_width = self.frame_width * self.cols
            sheet_height = self.frame_height * self.rows
            sprite_sheet = Image.new('RGBA', (sheet_width, sheet_height), self.background_color)
            
            processed_frames = 0
            missing_frames = 0
            
            for anim_name, anim_config in self.animations.items():
                row = anim_config['row']
                expected_frames = anim_config['frames']
                
                if anim_name in found_frames:
                    frame_paths = found_frames[anim_name]
                    actual_frames = min(len(frame_paths), expected_frames)
                    
                    logger.info(f"处理动画 {anim_name}: {actual_frames}/{expected_frames} 帧")
                    
                    for frame_idx in range(actual_frames):
                        frame_path = frame_paths[frame_idx]
                        
                        try:
                            frame_img = Image.open(frame_path).convert('RGBA')
                            frame_img = frame_img.resize((self.frame_width, self.frame_height), 
                                                       Image.Resampling.NEAREST)
                            
                            x = frame_idx * self.frame_width
                            y = row * self.frame_height
                            
                            sprite_sheet.paste(frame_img, (x, y), frame_img)
                            processed_frames += 1
                            
                        except Exception as e:
                            logger.error(f"处理帧失败 {frame_path}: {e}")
                            missing_frames += 1
                    
                    if actual_frames < expected_frames:
                        missing_count = expected_frames - actual_frames
                        logger.warning(f"  动画 {anim_name} 缺失 {missing_count} 帧")
                        missing_frames += missing_count
                        
                else:
                    logger.warning(f"未找到动画 {anim_name} 的帧文件")
                    missing_frames += expected_frames
            
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            sprite_sheet.save(str(output_path), 'PNG')
            result["output_path"] = str(output_path)
            
            config_path = output_path.with_suffix('.json')
            self.generate_sprite_config(str(config_path), str(output_path))
            result["config_path"] = str(config_path)
            
            result.update({
                "success": True,
                "message": f"精灵表创建成功！已处理 {processed_frames} 帧，缺失 {missing_frames} 帧",
                "processed_frames": processed_frames,
                "missing_frames": missing_frames,
                "sheet_width": sheet_width,
                "sheet_height": sheet_height
            })
            
            return result
            
        except Exception as e:
            logger.error(f"创建精灵表失败: {e}")
            result["message"] = f"创建精灵表失败: {e}"
            return result
    
    def generate_sprite_config(self, config_path: str, sprite_path: str):
        """生成精灵表配置文件，描述生成的图片信息"""
        sprite_config = {
            "frame_width": self.frame_width,
            "frame_height": self.frame_height,
            "cols": self.cols,
            "rows": self.rows,
            "animations": {}
        }
        
        # 简化的动画配置格式：只记录行号和帧数（行号从1开始）
        for anim_name, anim_config in self.animations.items():
            sprite_config["animations"][anim_name] = {
                "row": anim_config["row"] + 1,  # 行号从1开始
                "frames": anim_config["frames"]
            }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(sprite_config, f, indent=2, ensure_ascii=False)