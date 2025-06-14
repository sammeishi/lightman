"""任务构造器
从一个视频文件构造出一个任务
"""

import glob
import os
from models import Task
import yaml
from paths import root_dir

def from_video_dir(video_dir: str):
    # 检查目录内是否有视频
    files = extract_files(video_dir)
    # 构造任务
    task = Task()
    task.video_file = files['video_file']
    task.video_dir = os.path.dirname(files['video_file'])
    task.config = generate_task_conf(files['conf_file'])
    # 输出目录
    task.output_dir = os.path.join(task.video_dir, '')
    os.makedirs(task.output_dir, exist_ok=True)
    return task

def generate_task_conf(confFile: str):
    """生成任务配置
    加载一个基础的配置文件，然后合并目录内的config.yaml
    """
    # 加载基本的配置
    baseConfFile = os.path.join(root_dir, 'base_conf.yaml')
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

def extract_files(video_dir: str):
    """提取视频文件信息
    从一个目录内查找视频文件并提取
    """
    # 查找视频文件，必须只有一个
    res = list(glob.iglob(os.path.join(video_dir, '*.mp4'))) + \
      list(glob.iglob(os.path.join(video_dir, '*.avi'))) + \
      list(glob.iglob(os.path.join(video_dir, '*.mkv'))) + \
      list(glob.iglob(os.path.join(video_dir, '*.mov'))) + \
      list(glob.iglob(os.path.join(video_dir, '*.wmv')))
    if len(res) != 1:
        raise Exception('cannot find video file!')
    # 拿到文件
    target_video_file = res[0]
    # 解析配置文件
    confFile = list(glob.iglob(os.path.join(video_dir, 'config.yaml')))
    confFile = confFile[0] if confFile else None
    # 返回
    return {
        'video_file': target_video_file,
        'conf_file': confFile,
    }