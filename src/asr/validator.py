import json
import opencc

# 检查
# 1. 不能重复，语音转文字会出现重复文本，属于bug
# 2. 不能出现繁体

class Validator:
    def __init__(self, copywriting_json_file: str):
        self.copywriting_json_file = copywriting_json_file
        self.marks = {}
        self.cc = opencc.OpenCC('t2s')
        self.run()

    # check
    def run(self):
        # 打开并读取 JSON 文件
        with open(self.copywriting_json_file, 'r', encoding='utf-8') as file:
            parts = json.load(file)
            # 循环
            latestText = ''
            for part in parts:
                pureText = part['text'].strip()
                # 重复检查
                self.check_repeat_per_line(latestText, pureText, part)
                # 繁体检查
                self.check_traditional(latestText, pureText, part)
                latestText = pureText

    # 检查重复
    # 是连续重复的
    def check_repeat_per_line(self, latestText: str, currText: str, part: dict):
        key = 'repeatCount'
        limitCount = 10
        if key not in self.marks:
            self.marks[key] = 0
        # 相等累加1
        if latestText == currText:
            self.marks[key] += 1
        else:
            self.marks[key] = 0
        # 超出
        if self.marks[key] > limitCount:
            raise Exception('repeat text: %s! start: %s limitCount: %s' % (currText, part['start'], limitCount))

    # 检查繁体字
    # SST的bug，可能会翻译成繁体字
    # 只要超过N个字 就算
    def check_traditional(self, latestText: str, currText: str, part: dict):
        key = 'traditionalCount'
        limitCount = 3
        if key not in self.marks:
            self.marks[key] = 0
        # 循环每个字
        for character in currText:
            converted_text = self.cc.convert(character)
            if converted_text != character:
                self.marks[key] += 1
        # 超出
        if self.marks[key] > limitCount:
            raise Exception('traditional text: %s! start: %s limitCount: %s' % (currText, part['start'], limitCount))