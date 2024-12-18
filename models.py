# 任务配置
class TaskConfig:
    noky: int = 0

# 任务上下文
# 存储数据，任务信息等
class Task:
    # 目标视频目录
    videoDir: str = ''
    # 目标视频文件
    videoFile: str = ''
    # 视频文件大小
    videoSize: int = 0
    # 提取出的音频
    audioFile: str = ''
    # 输出目录
    outputDir: str = ''
    # 文案,原始结构的。json
    copywritingJsonFile: str = ''
    # 格式化后的json文件
    formattingJsonFile: str = ''
    # 任务配置信息
    config: TaskConfig = None