#!/usr/bin/env python3
"""HD2D 精灵表拼接工具模块"""

import os
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class SpriteSheetComposer:
    """精灵表拼接器"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化精灵表拼接器
        
        Args:
            config: 配置字典，如果为None则使用默认配置
        """
        if config is None:
            config = self.get_default_config()
        
        self.config = config
        self.frame_width = self.config.get('frame_width', 64)
        self.frame_height = self.config.get('frame_height', 96)
        self.cols = self.config.get('cols', 8)
        self.rows = self.config.get('rows', 16)
        self.animations = self.config.get('animations', {})
        self.background_color = tuple(self.config.get('background_color', [0, 0, 0, 0]))
    
    @staticmethod
    def get_default_config() -> Dict:
        """获取默认配置"""
        return {
            "frame_width": 64,
            "frame_height": 96,
            "cols": 8,
            "rows": 16,
            "background_color": [0, 0, 0, 0],
            "animations": {
                "idle_down": {"row": 0, "frames": 8},
                "idle_left": {"row": 1, "frames": 8},
                "idle_right": {"row": 2, "frames": 8},
                "idle_up": {"row": 3, "frames": 8},
                "walk_down": {"row": 4, "frames": 8},
                "walk_left": {"row": 5, "frames": 8},
                "walk_right": {"row": 6, "frames": 8},
                "walk_up": {"row": 7, "frames": 8},
                "run_down": {"row": 8, "frames": 6},
                "run_left": {"row": 9, "frames": 6},
                "run_right": {"row": 10, "frames": 6},
                "run_up": {"row": 11, "frames": 6},
                "attack_down": {"row": 12, "frames": 4},
                "attack_left": {"row": 13, "frames": 4},
                "attack_right": {"row": 14, "frames": 4},
                "attack_up": {"row": 15, "frames": 4}
            }
        }
    
    def load_config_file(self, config_path: str) -> Dict:
        """从文件加载配置"""
        default_config = self.get_default_config()
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
                    logger.info(f"已加载配置文件: {config_path}")
            except Exception as e:
                logger.error(f"加载配置文件失败: {e}")
                logger.info("使用默认配置")
        
        return default_config
    
    def find_frames(self, input_dir: str) -> Dict[str, List[str]]:
        """
        扫描输入目录，按动画类型分组找到所有帧文件
        
        Args:
            input_dir: 输入目录路径
            
        Returns:
            Dict[动画名称, 帧文件路径列表]
        """
        input_path = Path(input_dir)
        if not input_path.exists():
            raise FileNotFoundError(f"输入目录不存在: {input_dir}")
        
        found_frames = {}
        
        for file_path in input_path.glob("*.png"):
            filename = file_path.stem
            parts = filename.split('_')
            
            if len(parts) >= 3:
                anim_name = '_'.join(parts[:-1])
                frame_num_str = parts[-1]
                
                try:
                    frame_num = int(frame_num_str)
                    if anim_name not in found_frames:
                        found_frames[anim_name] = []
                    found_frames[anim_name].append((frame_num, str(file_path)))
                except ValueError:
                    logger.warning(f"无法解析帧序号: {filename}")
        
        for anim_name in found_frames:
            found_frames[anim_name].sort(key=lambda x: x[0])
            found_frames[anim_name] = [path for _, path in found_frames[anim_name]]
        
        return found_frames
    
    def create_sprite_sheet(self, input_dir: str, output_path: str, 
                           generate_preview: bool = False) -> Dict:
        """
        创建精灵表
        
        Args:
            input_dir: 输入图片目录
            output_path: 输出精灵表路径
            generate_preview: 是否生成预览图
            
        Returns:
            Dict: 包含结果信息的字典
        """
        result = {
            "success": False,
            "message": "",
            "output_path": "",
            "preview_path": "",
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
            
            if generate_preview:
                preview_path = output_path.with_suffix('.preview.png')
                self.generate_preview(sprite_sheet, str(preview_path))
                result["preview_path"] = str(preview_path)
            
            config_path = output_path.with_suffix('.json')
            self.generate_godot_config(str(config_path), str(output_path))
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
    
    def generate_preview(self, sprite_sheet: Image.Image, preview_path: str):
        """生成带网格线的预览图"""
        preview = sprite_sheet.copy()
        draw = ImageDraw.Draw(preview)
        
        for col in range(self.cols + 1):
            x = col * self.frame_width
            draw.line([(x, 0), (x, preview.height)], fill=(255, 255, 255, 128), width=1)
        
        for row in range(self.rows + 1):
            y = row * self.frame_height
            draw.line([(0, y), (preview.width, y)], fill=(255, 255, 255, 128), width=1)
        
        try:
            font = ImageFont.load_default()
            for anim_name, anim_config in self.animations.items():
                row = anim_config['row']
                y = row * self.frame_height + 2
                draw.text((2, y), anim_name, fill=(255, 255, 0, 255), font=font)
        except:
            pass
        
        preview.save(preview_path, 'PNG')
    
    def generate_godot_config(self, config_path: str, sprite_path: str):
        """生成 Godot 项目可用的配置文件"""
        godot_config = {
            "frame_width": self.frame_width,
            "frame_height": self.frame_height,
            "fps": 12.0,
            "billboard_mode": True,
            "pixel_perfect": True,
            "texture_path": sprite_path.replace('\\', '/'),
            "animations": {}
        }
        
        for anim_name, anim_config in self.animations.items():
            godot_config["animations"][anim_name] = {
                "row": anim_config["row"],
                "frames": anim_config["frames"],
                "start_frame": 0
            }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(godot_config, f, indent=2, ensure_ascii=False)