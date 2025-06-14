import ffmpeg
from rich.console import Console
from urllib.parse import urlparse
import http.client

# 默认的console，全局共享
console = Console()

def print_video_info(videoFile):
    """打印视频文件信息
    """
    probe = ffmpeg.probe(videoFile)
    console.print('videoFile: {}'.format(videoFile))
    fmt = probe['format']
    bit_rate = int(fmt['bit_rate']) / 1000
    duration = float(fmt['duration'])
    size = int(fmt['size']) / 1024 / 1024
    video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)

    if video_stream is None:
        console.print('No video stream found!')
        return

    width = int(video_stream['width'])
    height = int(video_stream['height'])
    num_frames = int(video_stream['nb_frames'])
    fps = int(video_stream['r_frame_rate'].split('/')[0]) / int(video_stream['r_frame_rate'].split('/')[1])
    duration = float(video_stream['duration'])

    # 精简浮点数到两位小数
    bit_rate = round(bit_rate, 2)
    fps = round(fps, 2)
    size = round(size, 2)
    duration_minutes = int(duration) // 60
    duration_seconds = int(duration) % 60

    # 输出视频信息
    console.print(f'width: {width}')
    console.print(f'height: {height}')
    console.print(f'num_frames: {num_frames}')
    console.print(f'bit_rate: {bit_rate}k')
    console.print(f'fps: {fps}')
    console.print(f'size: {size}MB')
    console.print(f'duration: {int(duration)}s ({duration_minutes}m {duration_seconds}s)')


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