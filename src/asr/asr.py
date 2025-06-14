import os
from models import Task
from faster_whisper import WhisperModel
import json
from rich.progress import Progress
from .validator import Validator
from utils import console
import opencc

# 语音转文字
# sst服务
class ASR:
    # init
    def __init__(self, task: Task):
        self.cc = opencc.OpenCC('t2s')
        self.traditionalCount = 0
        self.task = task
        # 执行
        self.audio_to_text()

    # 转化成文本
    def audio_to_text(self):
        # 存在则跳过
        saveJsonFle = self.generate_save_json_file()
        if os.path.exists(saveJsonFle):
            console.print('copywriting json file already exist!')
        else:
            saveJsonFle = self.convert()
        # 检查文本正确性
        Validator(saveJsonFle)
        # 保存全文本
        saveWholeTxtFile = self.generate_save_whole_txt_file()
        if os.path.exists(saveWholeTxtFile):
            console.print('copywriting whole txt file already exist!')
        else:
            self.save_whole_txt(saveJsonFle)
        # 保存到task上
        self.task.copywriting_json_file = saveJsonFle

    # 转换
    def convert(self):
        saveFile = self.generate_save_json_file()
        # 使用转码模型，large实测反而更差空音频部分输出垃圾重复多行文字
        model_size = "medium"  # "large-v3"
        model = WhisperModel(model_size, device="cuda", compute_type="float16")
        segments, info = model.transcribe(self.task.audio_file, beam_size=15, language="zh",
                                          initial_prompt="以下是普通话的句子。请不要使用繁体")
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
            # 检查繁体
            self.check_traditional(segment.text, start, end)
            progress.update(pTask, completed=int(end))
        progress.stop()
        # 保存到文本
        with open(saveFile, 'w', encoding='utf-8') as json_file:
            json.dump(parts, json_file, indent=4, ensure_ascii=False)
        return saveFile

    # 全文本
    def save_whole_txt(self, saveJsonFle: str):
        with open(saveJsonFle, 'r', encoding='utf-8') as file:
            parts = json.load(file)
        textArr = []
        for part in parts:
            textArr.append(part["text"])
        wholeTxt = ' '.join(textArr)
        console.print('whole text: %s' % len(wholeTxt))
        # 保存到文本
        saveFile = self.generate_save_whole_txt_file()
        with open(saveFile, 'w', encoding='utf-8') as file:
            file.write(wholeTxt)
        console.print('save whole text: %s' % saveFile)

    # 保存文件名
    def generate_save_json_file(self):
        return '%s/copywriting.json' % (self.task.output_dir)

    # 保存文件名
    def generate_save_whole_txt_file(self):
        return '%s/copywriting.txt' % (self.task.output_dir)

    # 检查繁体字
    # SST的bug，可能会翻译成繁体字
    # 只要超过N个字 就算
    def check_traditional(self, currText: str, start: float, end: float):
        # 循环每个字
        for character in currText:
            converted_text = self.cc.convert(character)
            if converted_text != character:
                self.traditionalCount += 1
        # 超出
        if self.traditionalCount > 10:
            raise Exception('traditional text: %s! start: %s end: %s' % (currText, start, end))