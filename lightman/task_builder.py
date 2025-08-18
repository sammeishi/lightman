# file: media_task.py
"""
media_task.py

提供一个 `from_file` 函数，用于根据文件路径创建一个包含视频或音频路径的 Task。
优先级：视频文件 > 音频文件（仅支持 .wav, .mp3）
"""

import os

from models import Task

# 支持的扩展名
VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mkv', '.mov', '.flv', '.wmv', '.webm'}
AUDIO_EXTENSIONS = {'.wav', '.mp3'}

def _is_video_file(filepath):
    return os.path.isfile(filepath) and os.path.splitext(filepath)[1].lower() in VIDEO_EXTENSIONS

def _is_audio_file(filepath):
    return os.path.isfile(filepath) and os.path.splitext(filepath)[1].lower() in AUDIO_EXTENSIONS

def from_file(file_path):
    """
    根据输入路径创建 Task 对象。
    
    参数:
        file_path (str): 文件或文件夹路径
    
    返回:
        Task: 包含 video_path 或 audio_path 的 Task 实例
    """
    task = Task()

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"file path not exist: {file_path}")

    if os.path.isdir(file_path):
        task.root_path = file_path
        # 查找第一个视频文件
        for entry in os.scandir(file_path):
            if entry.is_file() and _is_video_file(entry.path):
                task.video_path = entry.path
                task.video_size = entry.stat().st_size  # 获取文件大小
                return task

        # 没有视频文件，查找第一个音频文件
        for entry in os.scandir(file_path):
            if entry.is_file() and _is_audio_file(entry.path):
                task.audio_path = entry.path
                task.audio_size = entry.stat().st_size  # 获取文件大小
                return task

    elif os.path.isfile(file_path):
        task.root_path = os.path.dirname(file_path)
        if _is_video_file(file_path):
            task.video_path = file_path
            task.video_size = os.path.getsize(file_path)
            return task
        elif _is_audio_file(file_path):
            task.audio_path = file_path
            task.audio_size = os.path.getsize(file_path)
            return task

    # 如果没有匹配的文件
    raise ValueError(f"cannot find video or audio file in path: {file_path}")