import glob
import os
from models import Task
import yaml


# 任务构造器
# 从一个视频文件构造
def fromVideoDir(videoDir: str):
    # 检查目录内是否有视频
    files = extractFiles(videoDir)
    # 构造任务
    task = Task()
    task.videoFile = files['videoFile']
    task.videoDir = os.path.dirname(files['videoFile'])
    task.config = generateTaskConf(files['confFile'])
    # 输出目录
    task.outputDir = os.path.join(task.videoDir, '')
    os.makedirs(task.outputDir, exist_ok=True)
    return task

# 生成一个任务的配置
# 加载一个基础的配置文件，然后合并视频目录内的config.yaml
def generateTaskConf(confFile: str):
    # 加载基本的配置
    baseConfFile = os.path.abspath('./baseConf.yaml')
    with open(baseConfFile, 'r', encoding='utf-8') as f:
        conf = yaml.safe_load(f)
    if conf is None:
        return None
    # 加载视频内的配置
    if confFile is not None:
        with open(confFile, 'r', encoding='utf-8') as f:
            overrideConf = yaml.safe_load(f)
            if overrideConf is not None:
                conf.update(overrideConf)
    return conf

# 提取一个目录内的文件信息
# 提取视频文件,配置文件
def extractFiles(videoDir: str):
    # 查找视频文件，必须只有一个
    res = list(glob.iglob(os.path.join(videoDir, '*.mp4'))) + \
      list(glob.iglob(os.path.join(videoDir, '*.avi'))) + \
      list(glob.iglob(os.path.join(videoDir, '*.mkv'))) + \
      list(glob.iglob(os.path.join(videoDir, '*.mov'))) + \
      list(glob.iglob(os.path.join(videoDir, '*.wmv')))
    if len(res) != 1:
        raise Exception('cannot find video file!')
    # 拿到文件
    targetVideoFile = res[0]
    # 解析配置文件
    confFile = list(glob.iglob(os.path.join(videoDir, 'config.yaml')))
    confFile = confFile[0] if confFile else None
    # 返回
    return {
        'videoFile': targetVideoFile,
        'confFile': confFile,
    }