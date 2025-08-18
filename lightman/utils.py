import os
from urllib.parse import urlparse
import http.client

from rich.console import Console
import cv2
import ffmpeg
from dotenv import load_dotenv, dotenv_values

from config.paths import root_path

# 默认的console，全局共享
console = Console()


def is_url_reachable(url, timeout=3):
    parsed_url = urlparse(url)
    host = parsed_url.hostname
    port = parsed_url.port
    path = parsed_url.path or '/'

    # Determine the connection class based on the scheme
    if parsed_url.scheme == 'https':
        conn = http.client.HTTPSConnection(host, port, timeout=timeout)
    else:
        conn = http.client.HTTPConnection(host, port, timeout=timeout)

    try:
        conn.request("GET", path)
        response = conn.getresponse()
        # Any response status is acceptable, just check if response is received
        return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False
    finally:
        conn.close()


def print_video_info(video_path):
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print(f"cannot open video {video_path}")
        return None

    # 获取信息
    infos = {}
    infos['fps'] = fps = cap.get(cv2.CAP_PROP_FPS)  # 帧率
    infos['frames'] = frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))  # 总帧数
    infos['width'] = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))  # 宽度
    infos['height'] = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))  # 高度
    infos['duration'] = round(frame_count / fps if fps > 0 else 0)  # 时长（秒）
    infos['size'] = os.path.getsize(video_path)

    cap.release()

    for key, value in infos.items():
        val = value
        if key == 'size':
            val = f"{value / 1024 / 1024:.2f} MB"
        console.print(f"{key}: {val}")

    return None


def load_prompt(file, replace_map: dict = None) -> str:
    """加载prompt
    可以实现对prompt的关键词进行替换
    关键词必须是用占位符号包裹，如 %var%
    """
    prompt = ''
    with open(file, 'r', encoding='utf-8') as f:
        prompt = f.read()
    # 替换表为空 则返回
    if replace_map is not None:
        # 按key长度排序（长key优先），避免短key嵌套在长key中被误替换
        sorted_keys = sorted(replace_map.keys(), key=lambda k: len(k), reverse=True)
        for key in sorted_keys:
            # 仅在键存在时进行替换
            if key in prompt:
                prompt = prompt.replace(key, replace_map[key])

    return prompt


def extract_audio(video_path: str, save_path: str):
    """提取音频从一个视频文件内"""

    ffmpeg.input(video_path).output(save_path, loglevel='quiet').run(overwrite_output=True)


def load_env(env_file_path, curr_env: str):
    """加载环境变量
    智能加载：
        根据传入env，如果是dev，则会加载base.env,dev.env
        否则加载base.env,prod.env
    优先级：
        高优先级env会覆盖低的，反观不会，下面从高到低排序
        1. 手动传入环境变量 使用export(linux)
        2. dev/prod
        3. base
    """

    # 文件映射
    env_name_map = {
        'base': 'base.env',
        'dev': 'dev.env',
        'prod': 'prod.env',
    }

    # 当前环境
    assert curr_env in env_name_map, f"APP_ENV_MODE must be one of {list(env_name_map.keys())}"

    # 加载基础的
    base_env = dotenv_values(os.path.join(env_file_path, env_name_map['base']))

    # 加载当前应用的
    app_env = dotenv_values(os.path.join(env_file_path, env_name_map[curr_env]))
    merged_env = {**base_env, **app_env}

    # cli
    cli_env = dict(os.environ)
    final_env = {**merged_env, **cli_env}

    # 设置环境变量（可选：更新系统环境）
    os.environ.update(final_env)