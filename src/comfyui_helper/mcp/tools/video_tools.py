"""
视频处理相关的 MCP 工具
"""

import logging
from pathlib import Path
from ...core.video_frame_extractor import VideoFrameExtractor

logger = logging.getLogger(__name__)


def register_video_tools(mcp):
    """注册视频处理相关的 MCP 工具"""
    
    @mcp.tool()
    def extract_video_frames(
        video_url: str,
        output_dir: str,
        fps: float = None,
        start_time: float = None,
        duration: float = None,
        frame_count: int = None,
        interval: float = None,
        extract_keyframes: bool = False,
        output_format: str = 'png',
        output_prefix: str = 'frame',
        quality: int = 2
    ) -> str:
        """
        从视频中提取帧图片
        
        Args:
            video_url: 视频文件路径或URL
            output_dir: 输出目录路径
            fps: 提取帧率（每秒提取多少帧），与 frame_count/interval 互斥
            start_time: 开始时间（秒）
            duration: 持续时间（秒）
            frame_count: 要提取的总帧数，与 fps/interval 互斥
            interval: 时间间隔（秒），每隔多少秒提取一帧，与 fps/frame_count 互斥
            extract_keyframes: 是否只提取关键帧（I帧）
            output_format: 输出图片格式（png, jpg, jpeg）
            output_prefix: 输出文件前缀
            quality: JPEG 质量（1-31，1 最高质量，仅对 jpg/jpeg 有效）
        
        Returns:
            处理结果信息
        """
        try:
            # 创建提取器
            extractor = VideoFrameExtractor()
            
            # 确保输出目录存在
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # 执行提取
            result = extractor.extract_frames(
                video_url=video_url,
                output_dir=str(output_path),
                fps=fps,
                start_time=start_time,
                duration=duration,
                frame_count=frame_count,
                interval=interval,
                extract_keyframes=extract_keyframes,
                output_format=output_format,
                output_prefix=output_prefix,
                quality=quality
            )
            
            if result['success']:
                response_text = f"""✅ 视频帧提取成功！

视频信息:
- 输入文件: {result['video_url']}
- 视频时长: {result['video_duration']:.2f} 秒
- 视频帧率: {result['video_fps']:.2f} fps
- 视频尺寸: {result['video_width']}x{result['video_height']}

提取信息:
- 输出目录: {result['output_dir']}
- 提取帧数: {result['frame_count']}
- 提取模式: {result['extraction_mode']}"""

                if result.get('fps'):
                    response_text += f"\n- 提取帧率: {result['fps']} fps"
                if result.get('interval'):
                    response_text += f"\n- 提取间隔: {result['interval']} 秒"
                if result.get('start_time'):
                    response_text += f"\n- 开始时间: {result['start_time']} 秒"
                if result.get('duration'):
                    response_text += f"\n- 持续时间: {result['duration']} 秒"
                
                response_text += f"""
- 输出格式: {result['output_format'].upper()}
- 文件前缀: {result['output_prefix']}"""
                
                if result['output_format'] in ['jpg', 'jpeg']:
                    response_text += f"\n- JPEG 质量: {31 - result['quality']}/30 (质量等级)"
                
                response_text += f"\n\n输出文件: {result['output_prefix']}_*.{result['output_format']}"
                
                return response_text
            else:
                return f"❌ {result['message']}"
                
        except Exception as e:
            logger.error(f"视频帧提取失败: {e}")
            return f"❌ 提取失败: {str(e)}"