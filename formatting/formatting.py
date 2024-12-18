# from formatting.doubaoAI import ask
from formatting.aliAI import ask
from models import Task
import json
from thefuzz import fuzz
import os
from formatting import saveDocx
from utils import console

# 文案重排版
# 对已经语音转文字过的文案进行分割章节，添加标点符号，修正错别字等
# #算法
#  AI的输入输出有字数限制，如qwen-long支持百万输出，但是输出大概7K字
#  本方案是这样：先分一个最大字数的块，让AI去分割出章节，去掉最后一个章节，在从最后一个章节继续
# #下个其实点
#   判定下一个格式化起始点比较重要，当前使用AI输出一个original，记录章节的开头20个字，然后拿最后一个章节的original
#   去搜索即可

class Formatting:
    # 构造
    def __init__(self, task: Task):
        # 分片处理每片最大字数
        self.partSize = 3000
        # 文案脚本
        self.copywritingJsonFile = task.copywritingJsonFile
        # 下一个分块的位置，AI返回后需要查找最后章节矫正
        self.nextPartPos = 0
        # 全部文字
        self.wholeText = self.getWholeText()
        # 处理后的章节
        self.chapterList = []
        # 任务
        self.task = task
        # 最大字数，测试用
        self.maxWords = 20000
        # 开始
        self.start()

    # 开始格式化
    # 分片后循环送给AI，让AI总结出章节
    # 根据最后一个章节修正下一个分片点
    def start(self):
        # 文件不存在则处理
        saveFile = self.getSaveFile()
        if not os.path.exists(saveFile):
            self.handle()
        else:
            print('json already exist %s ' % saveFile)
        # 更新文件
        self.task.formattingJsonFile = saveFile
        # 输出docx
        saveDocx.save(self.task)

    # 处理分片
    def handle(self):
        # 最大循环1K次,每次3K总字数都非常庞大了
        console.print('formatting...')
        for i in range(100):
            # 获取分块
            part = self.getNextPart()
            if part is None:
                break
            # console
            console.log('pos=%s part=%s whole=%s' % (self.nextPartPos, len(part), len(self.wholeText)))
            # 送给AI，并且更新位置。
            currErr = None
            tryCount = 3
            while tryCount > 0:
                try:
                    # 送给AI，拿到章节
                    chapterList = ask(part)
                    for chapter in chapterList:
                        self.chapterList.append(chapter)
                    # 更新下一个分块的位置
                    self.updateNextPosFromChapter(part, chapterList[-1])
                    currErr = None
                    break
                except Exception as e:
                    currErr = e
                    console.print('error, retry %s' % tryCount)
                tryCount -= 1
            # 最后一次还是报错了
            if currErr is not None:
                raise currErr
            # 最后一个part 退出循环
            if len(part) < self.partSize:
                break
            # 最大字数
            if self.maxWords != 0 and self.nextPartPos >= self.maxWords:
                console.print('already to maxWords %s ! exit!' % self.maxWords)
                break
        # 保存到文本
        saveFile = self.getSaveFile()
        with open(saveFile, 'w', encoding='utf-8') as json_file:
            json.dump(self.chapterList, json_file, indent=4, ensure_ascii=False)

    # 根据最后的章节，查找下一个pos
    # 分片太小会导致bug，每一个分片必须分数多个章节才行！
    def updateNextPosFromChapter(self, part, chapter):
        findStr = chapter['content'][0:20]
        pos = self.fuzzyMatchStr(part, findStr)
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

    # 查找文本中以指定字符串开头的最佳匹配
    def fuzzyMatchStr(self, text, pattern, threshold=70):
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

    # 获取下一个分块
    def getNextPart(self):
        if self.nextPartPos >= len(self.wholeText):
            return None
        text = self.wholeText[self.nextPartPos:self.nextPartPos + self.partSize]
        return text

    # 获取完整的文本
    # 只添加空格，不添加任何其他标点符号
    def getWholeText(self) -> str:
        # 打开并读取 JSON 文件
        texts = []
        with open(self.copywritingJsonFile, 'r', encoding='utf-8') as file:
            parts = json.load(file)
            for part in parts:
                texts.append(part['text'])
        return " ".join(texts)

    # 获取保存文件
    def getSaveFile(self):
        return '%s/formatting.json' % (self.task.outputDir)