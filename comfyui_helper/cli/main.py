#!/usr/bin/env python3
"""
ComfyUI Helper 统一命令行入口
"""

import sys
import argparse
from pathlib import Path

def run_gif_maker_gui():
    """运行 GIF 制作器 GUI"""
    import sys
    # 清除命令行参数，避免传递给 gif_maker_gui
    old_argv = sys.argv
    sys.argv = [sys.argv[0]]
    try:
        from .gif_maker_gui import main as gif_main
        gif_main()
    finally:
        sys.argv = old_argv

def main():
    """主入口函数"""
    parser = argparse.ArgumentParser(
        prog='cfh',
        description='ComfyUI Helper 命令行工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  cfh gif-maker     启动 GIF 制作器 Web GUI
  cfh --help        显示帮助信息
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # GIF Maker 命令
    gif_parser = subparsers.add_parser(
        'gif-maker',
        help='启动 GIF 制作器 Web GUI'
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    if args.command == 'gif-maker':
        run_gif_maker_gui()
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()