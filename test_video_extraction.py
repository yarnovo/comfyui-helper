#!/usr/bin/env python3
"""
测试视频帧提取工具
"""

from src.comfyui_helper.video_frame_extractor import VideoFrameExtractor
from pathlib import Path
import tempfile

def test_video_extraction():
    print("测试视频帧提取工具")
    print("=" * 50)
    
    # 创建临时输出目录
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir) / "test_frames"
        output_dir.mkdir()
        
        # 创建测试视频（使用 ffmpeg 生成）
        test_video = Path(temp_dir) / "test_video.mp4"
        
        # 生成一个简单的测试视频（5秒，彩色条纹）
        import subprocess
        cmd = [
            "ffmpeg",
            "-f", "lavfi",
            "-i", "testsrc=duration=5:size=320x240:rate=30",
            "-pix_fmt", "yuv420p",
            str(test_video)
        ]
        
        print("生成测试视频...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"生成测试视频失败: {result.stderr}")
            return
        
        print(f"测试视频已生成: {test_video}")
        print()
        
        # 测试提取器
        extractor = VideoFrameExtractor()
        
        # 1. 获取视频信息
        print("1. 获取视频信息:")
        info = extractor.get_video_info(str(test_video))
        print(f"   时长: {info['duration']:.2f} 秒")
        print(f"   帧率: {info['fps']:.2f} fps")
        print(f"   分辨率: {info['width']}x{info['height']}")
        print(f"   总帧数: {info['total_frames']}")
        print()
        
        # 2. 按帧率提取
        print("2. 按帧率提取（每秒1帧）:")
        result = extractor.extract_frames(
            video_path=str(test_video),
            output_dir=str(output_dir / "fps"),
            fps=1
        )
        print(f"   成功: {result['success']}")
        print(f"   提取帧数: {result['frame_count']}")
        print()
        
        # 3. 按帧数提取
        print("3. 按总帧数提取（10帧）:")
        result = extractor.extract_frames(
            video_path=str(test_video),
            output_dir=str(output_dir / "count"),
            frame_count=10
        )
        print(f"   成功: {result['success']}")
        print(f"   提取帧数: {result['frame_count']}")
        print()
        
        # 4. 按时间间隔提取
        print("4. 按时间间隔提取（每0.5秒）:")
        result = extractor.extract_frames_by_interval(
            video_path=str(test_video),
            output_dir=str(output_dir / "interval"),
            interval=0.5
        )
        print(f"   成功: {result['success']}")
        print(f"   提取帧数: {result['frame_count']}")
        print()
        
        # 5. 提取关键帧
        print("5. 提取关键帧:")
        result = extractor.extract_keyframes(
            video_path=str(test_video),
            output_dir=str(output_dir / "keyframes")
        )
        print(f"   成功: {result['success']}")
        print(f"   提取帧数: {result['frame_count']}")
        print()
        
        print("=" * 50)
        print("测试完成！")

if __name__ == "__main__":
    test_video_extraction()