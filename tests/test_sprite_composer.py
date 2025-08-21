#!/usr/bin/env python3
"""
精灵图合成工具测试
使用 examples 中的测试数据进行测试
"""

import unittest
import sys
from pathlib import Path
import shutil
import json
from PIL import Image

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.comfyui_helper.sprite_composer import SpriteSheetComposer


class TestSpriteSheetComposer(unittest.TestCase):
    """精灵图合成器测试类"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试环境"""
        cls.example_project = Path("examples/sprite_sheet")
        cls.output_base_dir = Path("examples/sprite_sheet/output_test")
        
        # 验证示例项目是否存在
        if not cls.example_project.exists():
            raise FileNotFoundError(f"示例项目不存在: {cls.example_project}，请检查 examples 目录")
        
        # 创建合成器实例
        cls.composer = SpriteSheetComposer()
    
    
    def setUp(self):
        """每个测试前的准备"""
        # 创建输出目录
        self.output_base_dir.mkdir(parents=True, exist_ok=True)
    
    def test_load_config(self):
        """测试加载配置文件"""
        print("\n测试: 加载配置文件")
        
        config_path = self.example_project / "config.json"
        config = self.composer.load_config_file(str(config_path))
        
        # 验证配置内容
        self.assertIn("frame_width", config)
        self.assertIn("frame_height", config)
        self.assertIn("cols", config)
        self.assertIn("rows", config)
        self.assertIn("animations", config)
        
        print(f"  ✅ 成功加载配置: {config['cols']}x{config['rows']} 网格")
    
    def test_create_sprite_sheet(self):
        """测试创建精灵表"""
        print("\n测试: 创建精灵表")
        
        # 加载配置
        config_path = self.example_project / "config.json"
        config = self.composer.load_config_file(str(config_path))
        composer = SpriteSheetComposer(config)
        
        # 创建精灵表
        input_dir = self.example_project / "input_frames"
        output_path = self.output_base_dir / "test_spritesheet.png"
        
        result = composer.create_sprite_sheet(
            str(input_dir),
            str(output_path),
            generate_preview=False
        )
        
        self.assertTrue(result["success"])
        self.assertGreater(result["processed_frames"], 0)
        
        # 验证输出文件
        self.assertTrue(Path(result["output_path"]).exists())
        self.assertTrue(Path(result["config_path"]).exists())
        
        # 验证图片尺寸
        img = Image.open(result["output_path"])
        expected_width = config["frame_width"] * config["cols"]
        expected_height = config["frame_height"] * config["rows"]
        self.assertEqual(img.size, (expected_width, expected_height))
        
        print(f"  ✅ 创建精灵表: {img.size[0]}x{img.size[1]}, {result['processed_frames']} 帧")
    
    def test_create_with_preview(self):
        """测试创建带预览的精灵表"""
        print("\n测试: 创建带预览的精灵表")
        
        config_path = self.example_project / "config.json"
        config = self.composer.load_config_file(str(config_path))
        composer = SpriteSheetComposer(config)
        
        input_dir = self.example_project / "input_frames"
        output_path = self.output_base_dir / "preview_spritesheet.png"
        
        result = composer.create_sprite_sheet(
            str(input_dir),
            str(output_path),
            generate_preview=True
        )
        
        self.assertTrue(result["success"])
        self.assertIn("preview_path", result)
        self.assertTrue(Path(result["preview_path"]).exists())
        
        print(f"  ✅ 创建了预览图: {Path(result['preview_path']).name}")
    
    def test_godot_config_generation(self):
        """测试Godot配置文件生成"""
        print("\n测试: Godot配置文件生成")
        
        config_path = self.example_project / "config.json"
        config = self.composer.load_config_file(str(config_path))
        composer = SpriteSheetComposer(config)
        
        input_dir = self.example_project / "input_frames"
        output_path = self.output_base_dir / "godot_test.png"
        
        result = composer.create_sprite_sheet(
            str(input_dir),
            str(output_path),
            generate_preview=False
        )
        
        # 加载并验证Godot配置
        godot_config_path = Path(result["config_path"])
        self.assertTrue(godot_config_path.exists())
        
        with open(godot_config_path, "r") as f:
            godot_config = json.load(f)
        
        # 验证配置结构
        self.assertIn("frame_width", godot_config)
        self.assertIn("frame_height", godot_config)
        self.assertIn("animations", godot_config)
        
        # 验证动画信息
        animations = godot_config["animations"]
        self.assertGreater(len(animations), 0)
        
        # 验证动画结构
        first_anim_key = list(animations.keys())[0]
        first_anim = animations[first_anim_key]
        self.assertIn("row", first_anim)
        self.assertIn("frames", first_anim)
        self.assertIn("start_frame", first_anim)
        
        print(f"  ✅ Godot配置包含 {len(animations)} 个动画定义")
    
    def test_missing_frames_handling(self):
        """测试缺失帧处理"""
        print("\n测试: 缺失帧处理")
        
        # 创建有缺失帧的项目
        missing_project = Path("examples/test_missing_frames")
        input_dir = missing_project / "input_frames"
        input_dir.mkdir(parents=True, exist_ok=True)
        
        # 只创建部分帧
        img = Image.new('RGBA', (32, 48), (200, 100, 100))
        img.save(input_dir / "test_anim_001.png")
        img.save(input_dir / "test_anim_003.png")  # 缺少002
        
        config = {
            "frame_width": 32,
            "frame_height": 48,
            "cols": 4,
            "rows": 1,
            "background_color": [255, 255, 255, 255],
            "animations": {
                "test": {"row": 0, "frames": 4}
            }
        }
        
        composer = SpriteSheetComposer(config)
        output_path = self.output_base_dir / "missing_frames.png"
        
        result = composer.create_sprite_sheet(
            str(input_dir),
            str(output_path),
            generate_preview=False
        )
        
        self.assertTrue(result["success"])
        self.assertGreater(result["missing_frames"], 0)
        
        print(f"  ✅ 处理了 {result['missing_frames']} 个缺失帧")
        
        # 清理
        shutil.rmtree(missing_project)
    
    def test_default_config(self):
        """测试默认配置"""
        print("\n测试: 使用默认配置")
        
        # 创建没有配置文件的项目
        no_config_project = Path("examples/test_no_config")
        input_dir = no_config_project / "input_frames"
        input_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建测试帧
        for i in range(1, 5):
            img = Image.new('RGBA', (64, 96), (100, 200, 150))
            img.save(input_dir / f"default_test_{i:03d}.png")
        
        # 使用默认配置
        composer = SpriteSheetComposer()
        output_path = self.output_base_dir / "default_config.png"
        
        result = composer.create_sprite_sheet(
            str(input_dir),
            str(output_path),
            generate_preview=False
        )
        
        self.assertTrue(result["success"])
        
        print("  ✅ 使用默认配置创建精灵表")
        
        # 清理
        shutil.rmtree(no_config_project)
    
    def test_custom_background_color(self):
        """测试自定义背景颜色"""
        print("\n测试: 自定义背景颜色")
        
        config = {
            "frame_width": 32,
            "frame_height": 48,
            "cols": 2,
            "rows": 2,
            "background_color": [255, 0, 0, 255],  # 红色背景
            "animations": {
                "test": {"row": 0, "frames": 2}
            }
        }
        
        composer = SpriteSheetComposer(config)
        
        # 创建测试帧
        test_project = Path("examples/test_bg_color")
        input_dir = test_project / "input_frames"
        input_dir.mkdir(parents=True, exist_ok=True)
        
        for i in range(1, 3):
            img = Image.new('RGBA', (32, 48), (100, 150, 200, 128))  # 半透明
            img.save(input_dir / f"test_{i:03d}.png")
        
        output_path = self.output_base_dir / "red_background.png"
        
        result = composer.create_sprite_sheet(
            str(input_dir),
            str(output_path),
            generate_preview=False
        )
        
        self.assertTrue(result["success"])
        
        # 验证背景颜色
        img = Image.open(result["output_path"])
        # 检查空白区域的颜色（应该是红色）
        pixel = img.getpixel((config["cols"] * config["frame_width"] - 1, 
                            config["rows"] * config["frame_height"] - 1))
        self.assertEqual(pixel[:3], (255, 0, 0))  # RGB应该是红色
        
        print("  ✅ 应用了自定义背景颜色")
        
        # 清理
        shutil.rmtree(test_project)
    
    def test_existing_project(self):
        """测试使用现有的character_sprite项目"""
        print("\n测试: 使用现有示例项目")
        
        existing_project = Path("examples/character_sprite")
        
        if not existing_project.exists():
            print("  ⚠️  示例项目不存在，跳过测试")
            return
        
        config_path = existing_project / "config.json"
        if config_path.exists():
            config = self.composer.load_config_file(str(config_path))
            composer = SpriteSheetComposer(config)
        else:
            composer = SpriteSheetComposer()
        
        input_dir = existing_project / "input_frames"
        output_path = self.output_base_dir / "existing_project.png"
        
        result = composer.create_sprite_sheet(
            str(input_dir),
            str(output_path),
            generate_preview=True
        )
        
        self.assertTrue(result["success"])
        self.assertGreater(result["processed_frames"], 0)
        
        print(f"  ✅ 处理现有项目: {result['processed_frames']} 帧")
    
    @classmethod
    def tearDownClass(cls):
        """清理测试环境"""
        # 清理测试输出
        if cls.output_base_dir.exists():
            shutil.rmtree(cls.output_base_dir)
        
        print("\n精灵图合成测试完成，已清理测试输出")


if __name__ == "__main__":
    # 运行测试
    unittest.main(verbosity=2)