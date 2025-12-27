import os
import json

import opencc
from faster_whisper import WhisperModel
from rich.progress import Progress

from models import Task
from utils import console

# 指定离线
# 必须已经下载过，否则关比他
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"


class ASR:
    """
    音频转文字功能
    """

    def __init__(self, task: Task):
        self.cc = opencc.OpenCC('t2s')
        self.task = task
        self.result_json_path = os.path.join(task.root_path, 'asr.json')
        self.repeat_check_last_text = ''
        self.repeat_check_count = 0
        self.traditional_count = 0
        # 执行
        self.start()

    def start(self):
        """开始转换"""

        # 保存到task上
        self.task.asr_json_path = self.result_json_path
        console.print(self.result_json_path)

        # 存在则跳过
        if os.path.exists(self.result_json_path):
            console.print(f'already exist!')
            return

        # 开始转换，并检查
        self._convert()

    # 转换
    def _convert(self):

        # 使用转码模型，large实测反而更差空音频部分输出垃圾重复多行文字
        init_prompt = '以下是普通话的句子。请不要使用繁体'
        model_size = "medium"  # "large-v3"
        model = WhisperModel(model_size, device="cuda", compute_type="float16")
        audio = self.task.audio_path
        segments, info = model.transcribe(audio, beam_size=15, language="zh", initial_prompt=init_prompt)

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
            self._check_traditional(segment.text, start, end)
            # 重复性检查
            self._check_repeat(segment.text, start, end)
            # 进度
            progress.update(pTask, completed=int(end))

        # 进度条完成
        progress.update(pTask, completed=progress.tasks[pTask].total)
        progress.stop()

        # 保存json
        with open(self.result_json_path, 'w', encoding='utf-8') as json_file:
            json.dump(parts, json_file, indent=4, ensure_ascii=False)

    def _check_traditional(self, curr_text: str, start: float, end: float):
        """检查繁体字
        faster_whisper的bug，会翻译出繁体字
        必须在每个片段转换后都检查一次
        """

        # 更新繁体字计数
        for character in curr_text:
            converted_text = self.cc.convert(character)
            if converted_text != character:
                self.traditional_count += 1
        # 超出
        if self.traditional_count > 10:
            raise Exception('traditional text: %s! start: %s end: %s' % (curr_text, start, end))

    def _check_repeat(self, curr_text: str, start: float, end: float):
        """检查重复性
        faster_whisper的bug会转换出重复率很高的句子
        必须在每个片段转换后都检查一次
        必须是连续性的
        """

        repeat_limit = 5

        pure_text = curr_text.strip()
        if not pure_text:
            return

        if pure_text != self.repeat_check_last_text:
            self.repeat_check_last_text = pure_text
            self.repeat_check_count = 0
        else:
            self.repeat_check_count += 1

        # 检查
        if self.repeat_check_count > repeat_limit:
            raise Exception('repeat text: %s! start: %s end: %s' % (curr_text, start, end))
