#!/usr/bin/env python3
"""
视频帧提取工具测试
使用 examples 中的测试数据进行测试
"""

import unittest
import sys
from pathlib import Path
import shutil
import json

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.comfyui_helper.video_frame_extractor import VideoFrameExtractor


class TestVideoFrameExtractor(unittest.TestCase):
    """视频帧提取器测试类"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试环境"""
        cls.test_video = Path("examples/video_extraction/sample_video.mp4")
        cls.output_base_dir = Path("examples/video_extraction/output_frames")
        
        # 验证测试视频是否存在
        if not cls.test_video.exists():
            raise FileNotFoundError(f"测试视频不存在: {cls.test_video}，请先运行 scripts/prepare_test_data.py")
        
        # 创建提取器实例
        cls.extractor = VideoFrameExtractor()
    
    def setUp(self):
        """每个测试前的准备"""
        # 清理输出目录
        if self.output_base_dir.exists():
            shutil.rmtree(self.output_base_dir)
        self.output_base_dir.mkdir(parents=True, exist_ok=True)
    
    def test_video_info(self):
        """测试获取视频信息"""
        print("\n测试: 获取视频信息")
        
        info = self.extractor.get_video_info(str(self.test_video))
        
        # 验证返回的信息
        self.assertIn("duration", info)
        self.assertIn("fps", info)
        self.assertIn("total_frames", info)
        self.assertIn("width", info)
        self.assertIn("height", info)
        self.assertIn("codec", info)
        
        # 验证值的合理性
        self.assertGreater(info["duration"], 0)
        self.assertGreater(info["fps"], 0)
        self.assertGreater(info["width"], 0)
        self.assertGreater(info["height"], 0)
        
        print(f"  ✅ 视频信息: {info['duration']:.1f}秒, {info['fps']:.1f}fps, {info['width']}x{info['height']}")
    
    def test_extract_by_fps(self):
        """测试按帧率提取"""
        print("\n测试: 按帧率提取")
        
        output_dir = self.output_base_dir / "fps_test"
        
        result = self.extractor.extract_frames(
            video_path=str(self.test_video),
            output_dir=str(output_dir),
            fps=2  # 每秒2帧
        )
        
        self.assertTrue(result["success"])
        self.assertGreater(result["frame_count"], 0)
        
        # 验证文件是否存在
        output_files = list(output_dir.glob("*.png"))
        self.assertEqual(len(output_files), result["frame_count"])
        
        # 预期帧数基于视频时长和fps
        expected_frames = int(result["video_info"]["duration"] * 2)
        self.assertAlmostEqual(result["frame_count"], expected_frames, delta=1)
        
        print(f"  ✅ 提取了 {result['frame_count']} 帧 (fps=2)")
    
    def test_extract_by_frame_count(self):
        """测试按帧数提取"""
        print("\n测试: 按帧数提取")
        
        # 使用示例视频
        output_dir = self.output_base_dir / "count_test"
        
        target_count = 15
        result = self.extractor.extract_frames(
            video_path=str(self.test_video),
            output_dir=str(output_dir),
            frame_count=target_count
        )
        
        self.assertTrue(result["success"])
        self.assertEqual(result["frame_count"], target_count)
        
        # 验证文件
        output_files = list(output_dir.glob("*.png"))
        self.assertEqual(len(output_files), target_count)
        
        print(f"  ✅ 提取了 {result['frame_count']} 帧 (目标={target_count})")
    
    def test_extract_by_interval(self):
        """测试按时间间隔提取"""
        print("\n测试: 按时间间隔提取")
        
        # 使用示例视频
        output_dir = self.output_base_dir / "interval_test"
        
        result = self.extractor.extract_frames_by_interval(
            video_path=str(self.test_video),
            output_dir=str(output_dir),
            interval=0.5  # 每0.5秒一帧
        )
        
        self.assertTrue(result["success"])
        
        # 预期帧数基于视频时长和间隔
        expected_frames = int(result["video_info"]["duration"] / 0.5)
        self.assertAlmostEqual(result["frame_count"], expected_frames, delta=1)
        
        print(f"  ✅ 提取了 {result['frame_count']} 帧 (间隔=0.5秒)")
    
    def test_extract_keyframes(self):
        """测试提取关键帧"""
        print("\n测试: 提取关键帧")
        
        # 使用示例视频
        output_dir = self.output_base_dir / "keyframes_test"
        
        result = self.extractor.extract_keyframes(
            video_path=str(self.test_video),
            output_dir=str(output_dir)
        )
        
        self.assertTrue(result["success"])
        self.assertGreater(result["frame_count"], 0)
        
        print(f"  ✅ 提取了 {result['frame_count']} 个关键帧")
    
    def test_extract_with_time_range(self):
        """测试时间范围提取"""
        print("\n测试: 时间范围提取")
        
        # 使用示例视频
        output_dir = self.output_base_dir / "time_range_test"
        
        result = self.extractor.extract_frames(
            video_path=str(self.test_video),
            output_dir=str(output_dir),
            start_time=1,  # 从第1秒开始
            duration=2,    # 持续2秒
            fps=3         # 每秒3帧
        )
        
        self.assertTrue(result["success"])
        
        # 预期6帧（2秒 * 3fps）
        self.assertEqual(result["frame_count"], 6)
        
        print(f"  ✅ 提取了 {result['frame_count']} 帧 (1-3秒, fps=3)")
    
    def test_extract_jpeg_format(self):
        """测试JPEG格式输出"""
        print("\n测试: JPEG格式输出")
        
        # 使用示例视频
        output_dir = self.output_base_dir / "jpeg_test"
        
        result = self.extractor.extract_frames(
            video_path=str(self.test_video),
            output_dir=str(output_dir),
            fps=1,
            output_format="jpg",
            quality=5
        )
        
        self.assertTrue(result["success"])
        
        # 验证输出格式
        output_files = list(output_dir.glob("*.jpg"))
        self.assertEqual(len(output_files), result["frame_count"])
        
        # 验证没有PNG文件
        png_files = list(output_dir.glob("*.png"))
        self.assertEqual(len(png_files), 0)
        
        print(f"  ✅ 提取了 {result['frame_count']} 个JPEG图片")
    
    def test_invalid_video_path(self):
        """测试无效视频路径"""
        print("\n测试: 无效视频路径处理")
        
        output_dir = self.output_base_dir / "invalid_test"
        
        with self.assertRaises(FileNotFoundError):
            self.extractor.extract_frames(
                video_path="non_existent_video.mp4",
                output_dir=str(output_dir),
                fps=1
            )
        
        print("  ✅ 正确处理了无效视频路径")
    
    def test_output_directory_creation(self):
        """测试输出目录自动创建"""
        print("\n测试: 输出目录自动创建")
        
        # 使用示例视频
        output_dir = self.output_base_dir / "deep" / "nested" / "dir"
        
        # 确保目录不存在
        self.assertFalse(output_dir.exists())
        
        result = self.extractor.extract_frames(
            video_path=str(self.test_video),
            output_dir=str(output_dir),
            frame_count=1
        )
        
        self.assertTrue(result["success"])
        self.assertTrue(output_dir.exists())
        
        print("  ✅ 自动创建了嵌套输出目录")
    
    @classmethod
    def tearDownClass(cls):
        """清理测试环境"""
        # 清理测试输出
        if cls.output_base_dir.exists():
            shutil.rmtree(cls.output_base_dir)
        print("\n视频帧提取测试完成，已清理测试输出")


if __name__ == "__main__":
    # 运行测试
    unittest.main(verbosity=2)