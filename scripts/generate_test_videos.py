#!/usr/bin/env python3
"""
为视频帧提取示例生成测试视频的脚本
专门为 examples/video_extraction 目录准备测试视频文件
"""

import subprocess
import json
from pathlib import Path
import sys

def create_test_video(output_path, duration=10, fps=30, size="640x480", pattern="testsrc"):
    """
    使用 ffmpeg 创建测试视频
    
    Args:
        output_path: 输出视频路径
        duration: 视频时长（秒）
        fps: 帧率
        size: 视频尺寸
        pattern: 测试图案类型 (testsrc, testsrc2, rgbtestsrc, smptebars)
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        "ffmpeg",
        "-y",  # 覆盖已存在的文件
        "-f", "lavfi",
        "-i", f"{pattern}=duration={duration}:size={size}:rate={fps}",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        str(output_path)
    ]
    
    print(f"生成测试视频: {output_path}")
    print(f"  - 时长: {duration}秒")
    print(f"  - 帧率: {fps}fps")
    print(f"  - 尺寸: {size}")
    print(f"  - 图案: {pattern}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"✅ 视频生成成功: {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 视频生成失败: {e.stderr}")
        return False


def generate_test_videos_for_examples():
    """为 examples/video_extraction 生成测试视频"""
    video_dir = Path("examples/video_extraction")
    video_dir.mkdir(exist_ok=True)
    
    print("=" * 60)
    print("为视频帧提取示例生成测试视频")
    print("=" * 60)
    
    # 生成示例视频（如果不存在）
    print("\n检查并生成示例视频:")
    sample_video = video_dir / "sample_video.mp4"
    if not sample_video.exists():
        create_test_video(sample_video, duration=5, fps=10, size="320x240", pattern="testsrc")
    else:
        print(f"✅ 示例视频已存在: {sample_video}")
    
    print("\n" + "=" * 60)
    print("视频生成完成！")
    print(f"示例视频目录: {video_dir}")
    print("=" * 60)

if __name__ == "__main__":
    # 检查 ffmpeg 是否安装
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ 错误：未找到 ffmpeg，请先安装 ffmpeg")
        print("  Ubuntu/Debian: sudo apt-get install ffmpeg")
        print("  macOS: brew install ffmpeg")
        print("  Windows: 下载并安装 ffmpeg")
        sys.exit(1)
    
    generate_test_videos_for_examples()