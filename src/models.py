class TaskConfig:
    """任务配置"""
    pass

class Task:
    """任务结构"""

    # 目标视频目录
    video_dir: str = ''
    # 目标视频文件
    video_file: str = ''
    # 视频文件大小
    video_size: int = 0
    # 提取出的音频
    audio_file: str = ''
    # 输出目录
    output_dir: str = ''
    # 文案,原始结构的。json
    copywriting_json_file: str = ''
    # 格式化后的json文件
    formatting_json_file: str = ''
    # 任务配置信息
    config: TaskConfig = None
