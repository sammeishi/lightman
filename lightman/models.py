from dataclasses import dataclass

@dataclass
class Task:
    """任务结构"""

    # 任务根目录
    root_path: str = ''
    # 视频路径，可能没有
    video_path: str = ''
    # 视频文件大小，单位bytes
    video_size: int = 0
    # 提取出的音频
    audio_path: str = ''
    # 音频文件大小，单位bytes
    audio_size: int = 0
    # 文案,原始结构的。json
    asr_json_path: str = ''
