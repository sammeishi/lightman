import os
import ffmpeg
from rich.console import Console
from urllib.parse import urlparse
import http.client
import re

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


def print_video_info(video_file):
    """打印视频文件信息"""
    probe = ffmpeg.probe(video_file)
    console.print(f'video_file: {video_file}')
    fmt = probe['format']
    bit_rate = int(fmt['bit_rate']) / 1000
    duration = float(fmt['duration'])
    size = int(fmt['size']) / 1024 / 1024
    video_stream = next((stream for stream in probe['streams']
                         if stream['codec_type'] == 'video'), None)

    if video_stream is None:
        console.print('No video stream found!')
        return

    width = int(video_stream['width'])
    height = int(video_stream['height'])

    # 优先使用 nb_frames，否则通过帧率计算
    try:
        num_frames = int(video_stream['nb_frames'])
    except KeyError:
        try:
            # 尝试从 r_frame_rate 计算
            fps_fraction = video_stream['r_frame_rate'].split('/')
            fps = float(fps_fraction[0]) / float(fps_fraction[1])
            num_frames = int(float(video_stream.get('duration', duration)) * fps)
            console.print(f"[yellow]警告: 使用估算帧数 ({num_frames})[/yellow]")
        except:
            # 解决方案2：若仍然失败，使用 OpenCV 获取（需要安装 opencv-python）
            try:
                import cv2
                cap = cv2.VideoCapture(video_file)
                num_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                cap.release()
                console.print(f"[yellow]警告: 使用 OpenCV 获取帧数 ({num_frames})[/yellow]")
            except ImportError:
                console.print("[red]错误: 无法获取帧数，请安装 opencv-python[/red]")
                return

    # 处理帧率计算
    if '/' in video_stream['r_frame_rate']:
        fps_parts = video_stream['r_frame_rate'].split('/')
        fps = float(fps_parts[0]) / float(fps_parts[1])
    else:
        fps = float(video_stream['r_frame_rate'])

    # 精简浮点数到两位小数
    bit_rate = round(bit_rate, 2)
    fps = round(fps, 2)
    size = round(size, 2)
    duration_minutes = int(duration) // 60
    duration_seconds = int(duration) % 60

    # 输出视频信息
    console.print(f'resolution: {width} x {height}')
    console.print(f'num_frames: {num_frames}')
    console.print(f'bit_rate: {bit_rate}k')
    console.print(f'fps: {fps}')
    console.print(f'size: {size}MB')
    console.print(f'duration: {int(duration)}s ({duration_minutes}m {duration_seconds}s)')


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
