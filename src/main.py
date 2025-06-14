"""
lightman项目入口
"""

import argparse
import task_generate
import extractAudio
from formatting.formatting import Formatting
from asr.asr import ASR
from formatting import formatting
from utils import print_video_info, console
import sys

# main
def main():
    args = parse_arguments()
    task = task_generate.from_video_dir(args['videoDir'])
    # 视频文件信息
    console.print('[yellow bold]\[video info]')
    print_video_info(task.videoFile)
    console.print('')
    # 分离音频
    console.print('[yellow bold]\[extract audio]')
    extractAudio.extract(task)
    console.print('')
    # 转成文字
    console.print('[yellow bold]\[ASR]')
    ASR(task)
    console.print('')
    # # 转换
    console.print('[yellow bold]\[formatting]')
    Formatting(task)
    console.print('')


# 解析命令行参数
def parse_arguments():
    # 定义一个ArgumentParser实例:
    parser = argparse.ArgumentParser()
    # 定义关键字参数:
    parser.add_argument('--vd', help='video dir', required=True)
    # 解析参数:
    args = parser.parse_args()
    return {'videoDir': args.vd}


if __name__ == '__main__':
    main()
