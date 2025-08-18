import argparse
import os.path

import tomli

import task_builder
from asr import ASR
from utils import extract_audio, print_video_info, console, load_env
from formatting.formatting import Formatting
from config.paths import config_path, root_path


# 命令行参数
parser = argparse.ArgumentParser()
parser.add_argument('-f', '--file', required=True)
parser.add_argument('-e', '--env', required=False)
cmd_args = parser.parse_args()

# 加载环境变量, 从命令行参数确定当前运行env
curr_env = cmd_args.env or 'prod'
assert curr_env in ['dev', 'prod'], f'env: {curr_env} not support!'
load_env(config_path, curr_env)
os.environ['APP_ENV'] = curr_env
console.print('')
print(f'APP_ENV {curr_env}')

# 读取版本号
with open(os.path.join(root_path, 'pyproject.toml'), "rb") as f:
    data = tomli.load(f)
    version = data['project']['version']
    os.environ['APP_VERSION'] = version
    print(f'APP_VERSION {version}')

# 构建本次task
task = task_builder.from_file(cmd_args.file)

# 视频文件信息
console.print('')
console.print('[yellow bold]\[video info]')
console.print(task.video_path or 'NO VIDEO')
if task.video_path:
    print_video_info(task.video_path)
else:
    console.print('NO VIDEO')

# 分离音频
console.print('')
console.print('[yellow bold]\[extract audio]')
if not task.audio_path:
    audio_path = os.path.join(task.root_path, 'audio.mp3')
    if not os.path.exists(audio_path):
        print('extracting...')
        extract_audio(task.video_path, str(audio_path))
    else:
        print('already extract')
    # 必须更新一次audio信息
    task.audio_path = audio_path
    task.audio_size = os.path.getsize(audio_path)
else:
    print('task already got!')

# 音频信息
console.print('')
console.print('[yellow bold]\[audio info]')
print(task.audio_path or 'NO AUDIO')
if task.audio_path:
    console.print(f'size: {task.audio_size / 1024 / 1024:.2f}Mb')

# 转成文字
console.print('')
console.print('[yellow bold]\[ASR]')
ASR(task)

# 格式化
console.print('')
console.print('[yellow bold]\[formatting]')
Formatting(task)
