"""文案重排版

对已经语音转文字过的文案进行分割章节，添加标点符号，修正错别字等

算法：
    AI的输入输出有字数限制，如qwen-long支持百万输出，但是输出大概7K字
    本方案是这样：先分一个最大字数的块，让AI去分割出章节，去掉最后一个章节，在从最后一个章节继续

下个起始点：
    判定下一个格式化起始点比较重要，当前使用AI输出一个original，记录章节的开头20个字，然后拿最后一个章节的original
    去搜索即可
"""

from llm import ask
from models import Task
import json
from thefuzz import fuzz
import os
from formatting import save_docx
from utils import console

class Formatting:
    # 构造
    def __init__(self, task: Task):
        # 分片处理每片最大字数
        self.part_size = 3000
        # 文案脚本
        self.copywritingJsonFile = task.copywritingJsonFile
        # 下一个分块的位置，AI返回后需要查找最后章节矫正
        self.nextPartPos = 0
        # 全部文字
        self.wholeText = self.get_whole_text()
        # 处理后的章节
        self.chapterList = []
        # 任务
        self.task = task
        # 是否已完成
        self.isComplete = False
        # 最大字数，测试用
        self.maxWords = 800000
        # 开始
        self.start()

    def start(self):
        """开始执行

        需要恢复上一次执行断开的地方
        分片后循环送给AI，让AI总结出章节
        根据最后一个章节修正下一个分片点
        """
        # 恢复
        self.recover()
        # 未完成则处理
        if not self.isComplete:
            self.handle()
        # 更新文件
        self.task.formattingJsonFile = self.get_write_files('formatting')
        # 输出docx
        save_docx.save(self.task)

    def recover(self):
        # 读取文件
        saveFile = self.get_write_files('formatting')
        if not os.path.exists(saveFile):
            return
        # 读取保存文件信息
        with open(saveFile, 'r', encoding='utf-8') as json_file:
            saveData = json.load(json_file)
            if saveData is not None:
                console.print('recover from %s' % saveData['nextPartPos'])
                self.isComplete = saveData['isComplete']
                self.nextPartPos = saveData['nextPartPos']
                self.chapterList = saveData['chapterList']

    def handle(self):
        console.print('formatting...')
        for i in range(1000):
            # 获取分块
            part = self.get_next_part()
            if part is None:
                break
            # console
            console.print('pos=%s part=%s whole=%s' % (self.nextPartPos, len(part), len(self.wholeText)))
            # 送给AI，并且更新位置。
            self.handle_part(part)
            # 是否完成
            self.isComplete = len(part) < self.part_size
            # 实时保存
            self.save_now()
            # 最后一个part 退出循环
            if self.isComplete:
                break
            # 最大字数
            if self.maxWords != 0 and self.nextPartPos >= self.maxWords:
                console.print('already to maxWords %s ! exit!' % self.maxWords)
                break

    def handle_part(self, part: str):
        """处理分片

        会更新下一个pos
        """
        currErr = None
        tryCount = 3
        prompt = self.load_prompt()
        while tryCount > 0:
            try:
                # 送给AI，拿到章节
                chapterList = ask(question=part, system_prompt=prompt, model='deepseek-v3', rep_format='json')
                for chapter in chapterList:
                    self.chapterList.append(chapter)
                # 更新下一个分块的位置
                self.update_next_pos_from_chapter(part, chapterList[-1])
                currErr = None
                break
            except Exception as e:
                currErr = e
                console.print('error, retry %s' % tryCount)
            tryCount -= 1
        # 最后一次还是报错了
        if currErr is not None:
            raise currErr

    def load_prompt(self) -> str:
        curr = os.path.dirname(__file__)
        with open(os.path.join(curr,'prompt.txt'), 'r', encoding='utf-8') as f:
            return f.read()

    def update_next_pos_from_chapter(self, part, chapter):
        """查找下一个pos
        根据最后的章节,分片太小会导致bug，每一个分片必须分数多个章节才行！
        """
        findStr = chapter['content'][0:20]
        pos = self.fuzzy_match_str(part, findStr)
        # 找不到
        if pos == -1:
            print('********error************')
            console.print({
                "title": chapter['title'],
                "content": chapter['content'],
                "part": part,
            })
            raise Exception('cannot find pos in chapter。findStr: \n %s' % findStr)
        # 等于当前，说明卡住了
        if pos == 0:
            raise Exception('next pos fall into a cycle!')
        # 更新下一个分片pos，等同于最后一个章节
        self.nextPartPos += pos

    def fuzzy_match_str(self, text, pattern, threshold=70):
        """查找文本中以指定字符串开头的最佳匹配
        """
        best_match_pos = -1
        best_similarity = 0
        for i in range(len(text) - len(pattern) + 1):
            # 直接取固定长度的子串
            substring = text[i:i + len(pattern)]
            # 使用ratio()代替partial_ratio()，确保从开头匹配
            similarity = fuzz.ratio(substring, pattern)
            if similarity > best_similarity and similarity >= threshold:
                best_similarity = similarity
                best_match_pos = i

        return best_match_pos

    def get_next_part(self):
        if self.nextPartPos >= len(self.wholeText):
            return None
        text = self.wholeText[self.nextPartPos:self.nextPartPos + self.part_size]
        return text

    def get_whole_text(self) -> str:
        """获取完整的文本
        只添加空格，不添加任何其他标点符号
        """
        # 打开并读取 JSON 文件
        texts = []
        with open(self.copywritingJsonFile, 'r', encoding='utf-8') as file:
            parts = json.load(file)
            for part in parts:
                texts.append(part['text'])
        return " ".join(texts)

    def get_write_files(self, file: str):
        files = {
            "formatting": '%s/formatting.json' % (self.task.outputDir),
        }
        return files[file]

    def save_now(self):
        saveData = {
            "nextPartPos": self.nextPartPos, # 永远都是最新的，下次恢复可直接使用
            "isComplete": self.isComplete,
            "wholeLength": len(self.wholeText),
            "chapterList" : self.chapterList
        }
        with open(self.get_write_files('formatting'), 'w', encoding='utf-8') as json_file:
            json.dump(saveData, json_file, indent=4, ensure_ascii=False)