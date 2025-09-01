"""
视频帧提取工具
用于从视频文件中提取指定帧数的图片
"""

import logging
import subprocess
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class VideoFrameExtractor:
    """视频帧提取器"""
    
    def __init__(self):
        """初始化视频帧提取器"""
        self.ffmpeg_cmd = self._find_ffmpeg()
        if not self.ffmpeg_cmd:
            raise RuntimeError("未找到 ffmpeg，请确保已安装 ffmpeg")
    
    def _find_ffmpeg(self) -> Optional[str]:
        """查找系统中的 ffmpeg 命令"""
        for cmd in ["ffmpeg", "ffmpeg.exe"]:
            try:
                result = subprocess.run(
                    [cmd, "-version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    logger.info(f"找到 ffmpeg: {cmd}")
                    return cmd
            except (subprocess.SubprocessError, FileNotFoundError):
                continue
        return None
    
    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """获取视频信息"""
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            video_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            info = json.loads(result.stdout)
            
            # 提取视频流信息
            video_stream = None
            for stream in info.get("streams", []):
                if stream.get("codec_type") == "video":
                    video_stream = stream
                    break
            
            if not video_stream:
                raise ValueError("视频文件中未找到视频流")
            
            # 计算总帧数和时长
            duration = float(info.get("format", {}).get("duration", 0))
            fps = eval(video_stream.get("r_frame_rate", "0/1"))
            if isinstance(fps, (int, float)):
                fps = float(fps)
            else:
                fps = 0
            
            total_frames = int(video_stream.get("nb_frames", 0))
            if total_frames == 0 and duration > 0 and fps > 0:
                total_frames = int(duration * fps)
            
            return {
                "duration": duration,
                "fps": fps,
                "total_frames": total_frames,
                "width": video_stream.get("width", 0),
                "height": video_stream.get("height", 0),
                "codec": video_stream.get("codec_name", "unknown")
            }
            
        except subprocess.CalledProcessError as e:
            logger.error(f"获取视频信息失败: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"解析视频信息失败: {e}")
            raise
    
    def extract_frames(
        self,
        video_path: str,
        output_dir: str,
        fps: Optional[float] = None,
        start_time: Optional[float] = None,
        duration: Optional[float] = None,
        frame_count: Optional[int] = None,
        output_format: str = "png",
        output_prefix: str = "frame",
        quality: int = 2
    ) -> Dict[str, Any]:
        """
        从视频中提取帧
        
        Args:
            video_path: 视频文件路径
            output_dir: 输出目录路径
            fps: 提取帧率（每秒提取多少帧），None 表示提取所有帧
            start_time: 开始时间（秒）
            duration: 持续时间（秒）
            frame_count: 要提取的总帧数（与 fps 互斥）
            output_format: 输出图片格式（png, jpg, jpeg）
            output_prefix: 输出文件前缀
            quality: JPEG 质量（1-31，1 最高，仅对 jpg/jpeg 有效）
        
        Returns:
            包含处理结果的字典
        """
        video_path = Path(video_path)
        output_dir = Path(output_dir)
        
        # 验证输入
        if not video_path.exists():
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        # 创建输出目录
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 获取视频信息
        video_info = self.get_video_info(str(video_path))
        
        # 构建 ffmpeg 命令
        cmd = [self.ffmpeg_cmd, "-i", str(video_path)]
        
        # 添加开始时间
        if start_time is not None:
            cmd.extend(["-ss", str(start_time)])
        
        # 添加持续时间
        if duration is not None:
            cmd.extend(["-t", str(duration)])
        
        # 设置帧率或帧数
        if frame_count is not None:
            # 计算需要的帧率以获取指定数量的帧
            video_duration = duration if duration else video_info["duration"]
            if start_time:
                video_duration = min(video_duration, video_info["duration"] - start_time)
            
            if video_duration > 0:
                target_fps = frame_count / video_duration
                cmd.extend(["-vf", f"fps={target_fps}"])
        elif fps is not None:
            cmd.extend(["-vf", f"fps={fps}"])
        
        # 设置输出格式和质量
        if output_format.lower() in ["jpg", "jpeg"]:
            cmd.extend(["-q:v", str(quality)])
        
        # 设置输出文件模式
        output_pattern = str(output_dir / f"{output_prefix}_%06d.{output_format}")
        cmd.append(output_pattern)
        
        # 执行命令
        logger.info(f"执行命令: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            # 统计输出的帧数
            output_files = list(output_dir.glob(f"{output_prefix}_*.{output_format}"))
            output_files.sort()
            
            return {
                "success": True,
                "message": f"成功提取 {len(output_files)} 帧",
                "output_dir": str(output_dir),
                "frame_count": len(output_files),
                "files": [str(f) for f in output_files],
                "video_info": video_info
            }
            
        except subprocess.CalledProcessError as e:
            logger.error(f"提取帧失败: {e.stderr}")
            return {
                "success": False,
                "message": f"提取帧失败: {e.stderr}",
                "output_dir": str(output_dir),
                "frame_count": 0,
                "files": [],
                "video_info": video_info
            }
    
    def extract_frames_by_interval(
        self,
        video_path: str,
        output_dir: str,
        interval: float = 1.0,
        output_format: str = "png",
        output_prefix: str = "frame",
        quality: int = 2
    ) -> Dict[str, Any]:
        """
        按时间间隔提取帧
        
        Args:
            video_path: 视频文件路径
            output_dir: 输出目录路径
            interval: 时间间隔（秒）
            output_format: 输出图片格式
            output_prefix: 输出文件前缀
            quality: JPEG 质量
        
        Returns:
            包含处理结果的字典
        """
        fps = 1.0 / interval if interval > 0 else None
        return self.extract_frames(
            video_path=video_path,
            output_dir=output_dir,
            fps=fps,
            output_format=output_format,
            output_prefix=output_prefix,
            quality=quality
        )
    
    def extract_keyframes(
        self,
        video_path: str,
        output_dir: str,
        output_format: str = "png",
        output_prefix: str = "keyframe",
        quality: int = 2
    ) -> Dict[str, Any]:
        """
        提取关键帧（I帧）
        
        Args:
            video_path: 视频文件路径
            output_dir: 输出目录路径
            output_format: 输出图片格式
            output_prefix: 输出文件前缀
            quality: JPEG 质量
        
        Returns:
            包含处理结果的字典
        """
        video_path = Path(video_path)
        output_dir = Path(output_dir)
        
        # 验证输入
        if not video_path.exists():
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        # 创建输出目录
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 构建 ffmpeg 命令提取关键帧
        cmd = [
            self.ffmpeg_cmd,
            "-i", str(video_path),
            "-vf", "select='eq(pict_type,I)'",
            "-vsync", "vfr"
        ]
        
        # 设置输出格式和质量
        if output_format.lower() in ["jpg", "jpeg"]:
            cmd.extend(["-q:v", str(quality)])
        
        # 设置输出文件模式
        output_pattern = str(output_dir / f"{output_prefix}_%06d.{output_format}")
        cmd.append(output_pattern)
        
        # 执行命令
        logger.info(f"执行命令: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            # 统计输出的帧数
            output_files = list(output_dir.glob(f"{output_prefix}_*.{output_format}"))
            output_files.sort()
            
            return {
                "success": True,
                "message": f"成功提取 {len(output_files)} 个关键帧",
                "output_dir": str(output_dir),
                "frame_count": len(output_files),
                "files": [str(f) for f in output_files]
            }
            
        except subprocess.CalledProcessError as e:
            logger.error(f"提取关键帧失败: {e.stderr}")
            return {
                "success": False,
                "message": f"提取关键帧失败: {e.stderr}",
                "output_dir": str(output_dir),
                "frame_count": 0,
                "files": []
            }