import ffmpeg
from models import Task
import os
from rich.console import Console
import os
from utils import console


def extract(task: Task):
    # 输出音频文件
    file = os.path.join(task.output_dir, 'audio.mp3')
    if os.path.exists(file):
        console.print('audio already exist!')
    else:
        # 分离
        ffmpeg.input(task.video_file).output(file, loglevel='quiet').run(overwrite_output=True)
        console.print(file)
    # 打印文件信息
    console.print(file)
    size = os.path.getsize(file)
    size = int(size / 1024 / 1024)
    console.print(f'audio size: {size} MB')
    # 保存到任务上
    task.audio_file = file
