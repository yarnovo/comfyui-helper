#!/usr/bin/env python3
"""生成测试用的精灵帧图片"""

from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path

def create_sprite_frame(width=64, height=96, color=(100, 150, 200), text="", bg_color=(255, 255, 255, 0)):
    """创建单个精灵帧"""
    img = Image.new('RGBA', (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    
    # 绘制角色轮廓（简单的矩形表示）
    char_width = width * 0.6
    char_height = height * 0.8
    x1 = (width - char_width) / 2
    y1 = (height - char_height) / 2
    x2 = x1 + char_width
    y2 = y1 + char_height
    
    # 绘制身体
    draw.rectangle([x1, y1, x2, y2], fill=color, outline=(0, 0, 0), width=2)
    
    # 绘制头部
    head_size = width * 0.3
    head_x = width / 2 - head_size / 2
    head_y = y1 - head_size * 0.5
    draw.ellipse([head_x, head_y, head_x + head_size, head_y + head_size], 
                 fill=color, outline=(0, 0, 0), width=2)
    
    # 添加文字标签
    if text:
        try:
            # 尝试使用默认字体
            font = ImageFont.load_default()
        except:
            font = None
        
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        text_x = (width - text_width) / 2
        text_y = height - text_height - 5
        draw.text((text_x, text_y), text, fill=(0, 0, 0), font=font)
    
    return img

def generate_animation_frames(output_dir, animation_name, direction, num_frames, base_color):
    """生成某个动画的所有帧"""
    for i in range(1, num_frames + 1):
        # 创建渐变颜色效果（模拟动画）
        color_shift = int(20 * (i / num_frames))
        color = tuple(min(255, c + color_shift) for c in base_color)
        
        # 生成帧文件名
        filename = f"{animation_name}_{direction}_{i:03d}.png"
        filepath = output_dir / filename
        
        # 创建并保存精灵帧
        frame_text = f"{i}/{num_frames}"
        img = create_sprite_frame(color=color, text=frame_text)
        img.save(filepath)
        print(f"生成: {filename}")

def main():
    # 设置输出目录
    output_dir = Path("character_sprite/input_frames")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 定义动画配置
    animations = {
        "idle": {"frames": 8, "color": (100, 150, 200)},    # 蓝色系
        "walk": {"frames": 8, "color": (150, 200, 100)},    # 绿色系
        "run": {"frames": 6, "color": (200, 150, 100)},     # 橙色系
        "attack": {"frames": 4, "color": (200, 100, 100)}   # 红色系
    }
    
    directions = ["down", "left", "right", "up"]
    
    # 生成所有动画帧
    for anim_name, anim_config in animations.items():
        for direction in directions:
            full_anim_name = f"{anim_name}_{direction}"
            generate_animation_frames(
                output_dir,
                anim_name,
                direction,
                anim_config["frames"],
                anim_config["color"]
            )
    
    # 统计生成的文件
    generated_files = list(output_dir.glob("*.png"))
    print(f"\n总共生成了 {len(generated_files)} 个精灵帧文件")
    
    # 显示动画分组
    print("\n生成的动画类型:")
    for anim_name in animations:
        for direction in directions:
            pattern = f"{anim_name}_{direction}_*.png"
            count = len(list(output_dir.glob(pattern)))
            print(f"  {anim_name}_{direction}: {count} 帧")

if __name__ == "__main__":
    main()