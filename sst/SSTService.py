import os
from models import Task
from faster_whisper import WhisperModel
import json
from rich.progress import Progress
from sst.validator import Validator
from utils import console

# 语音转文字
# sst服务
class SSTService:
    # init
    def __init__(self, task: Task):
        self.task = task
        self.audioToText()

    # 转化成文本
    def audioToText(self):
        # 存在则跳过
        saveJsonFle = self.generateSaveJsonFile()
        if os.path.exists(saveJsonFle):
            console.print('copywriting json file already exist!')
        else:
            saveJsonFle = self.convert()
        # 检查文本正确性
        Validator(saveJsonFle)
        # 保存全文本
        saveWholeTxtFile = self.generateSaveWholeTxtFile()
        if os.path.exists(saveWholeTxtFile):
            console.print('copywriting whole txt file already exist!')
        else:
            self.saveWholeTxt(saveJsonFle)
        # 保存到task上
        self.task.copywritingJsonFile = saveJsonFle

    # 转换
    def convert(self):
        saveFile = self.generateSaveJsonFile()
        # 使用转码模型，large实测反而更差空音频部分输出垃圾重复多行文字
        model_size = "medium"  # "large-v3"
        model = WhisperModel(model_size, device="cuda", compute_type="float16")
        segments, info = model.transcribe(self.task.audioFile, beam_size=15, language="zh",
                                          initial_prompt="以下是普通话的句子,比如你们的，他们的。")
        duration = round(info.duration, 2)
        console.print('language = %s duration = %s' % (info.language, duration))
        # 进度条
        progress = Progress()
        pTask = progress.add_task("[cyan]STT:", total=int(duration))
        progress.start()
        # 流式提取
        parts = []
        for segment in segments:
            start = round(segment.start, 2)
            end = round(segment.end, 2)
            parts.append({"start": start, "end": end, "text": segment.text})
            progress.update(pTask, completed=int(end))
        progress.stop()
        # 保存到文本
        with open(saveFile, 'w', encoding='utf-8') as json_file:
            json.dump(parts, json_file, indent=4, ensure_ascii=False)
        return saveFile

    # 全文本
    def saveWholeTxt(self, saveJsonFle: str):
        with open(saveJsonFle, 'r', encoding='utf-8') as file:
            parts = json.load(file)
        textArr = []
        for part in parts:
            textArr.append(part["text"])
        wholeTxt = ' '.join(textArr)
        console.print('whole text: %s' % len(wholeTxt))
        # 保存到文本
        saveFile = self.generateSaveWholeTxtFile()
        with open(saveFile, 'w', encoding='utf-8') as file:
            file.write(wholeTxt)
        console.print('save whole text: %s' % saveFile)

    # 保存文件名
    def generateSaveJsonFile(self):
        return '%s/copywriting.json' % (self.task.outputDir)

    # 保存文件名
    def generateSaveWholeTxtFile(self):
        return '%s/copywriting.txt' % (self.task.outputDir)