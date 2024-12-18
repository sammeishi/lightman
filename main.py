import argparse
import taskGenerate
import extractAudio
from formatting.formatting import Formatting
from sst.SSTService import SSTService
from formatting import formatting
from utils import printVideoInfo, console

# main
def main():
    args = parseArguments()
    task = taskGenerate.fromVideoDir(args['videoDir'])
    # 视频文件信息
    console.print('[yellow bold]\[video info]')
    printVideoInfo(task.videoFile)
    console.print('')
    # 分离音频
    console.print('[yellow bold]\[extract audio]')
    extractAudio.extract(task)
    console.print('')
    # 转成文字
    console.print('[yellow bold]\[SST]')
    SSTService(task)
    console.print('')
    # # 转换
    console.print('[yellow bold]\[formatting]')
    Formatting(task)
    console.print('')

# 解析命令行参数
def parseArguments():
    # 定义一个ArgumentParser实例:
    parser = argparse.ArgumentParser()
    # 定义关键字参数:
    parser.add_argument('--vd', help='video dir', required=True)
    # 解析参数:
    args = parser.parse_args()
    return { 'videoDir': args.vd }


if __name__ == '__main__':
    main()