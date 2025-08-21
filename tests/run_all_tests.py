#!/usr/bin/env python3
"""
运行所有测试
"""

import sys
import unittest
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("ComfyUI Helper - 运行所有测试")
    print("=" * 60)
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加所有测试模块
    test_modules = [
        'tests.test_video_extractor',
        'tests.test_sprite_composer',
    ]
    
    for module in test_modules:
        try:
            suite.addTests(loader.loadTestsFromName(module))
            print(f"✅ 加载测试模块: {module}")
        except Exception as e:
            print(f"❌ 无法加载模块 {module}: {e}")
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 打印结果摘要
    print("\n" + "=" * 60)
    print("测试结果摘要")
    print("=" * 60)
    print(f"运行测试: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    if result.failures:
        print("\n失败的测试:")
        for test, traceback in result.failures:
            print(f"  - {test}")
    
    if result.errors:
        print("\n出错的测试:")
        for test, traceback in result.errors:
            print(f"  - {test}")
    
    # 返回是否成功
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)