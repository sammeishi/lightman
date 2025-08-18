import json
import os

from thefuzz import fuzz
import pydash

from llm import ask
from models import Task
from formatting import save_docx
from utils import console


class Formatting:
    """格式化
    对已经语音转文字过的文案进行分割章节，添加标点符号，修正错别字等

    算法：
        AI的输入输出有字数限制，如qwen-long支持百万输出，但是输出大概7K字
        本方案是这样：先分一个最大字数的块，让AI去分割出章节，去掉最后一个章节，在从最后一个章节继续

    下个起始点：
        判定下一个格式化起始点比较重要，当前使用AI输出一个original，记录章节的开头20个字，然后拿最后一个章节的original
        去搜索即可
    """

    def __init__(self, task: Task):
        self.task = task
        self.part_size = 5000
        self.max_part = 3000
        self.asr_json_path = task.asr_json_path
        self.next_part_pos = 0
        self.whole_text = self._get_whole_text()
        self.chapters = []
        self.is_complete = False
        self.max_words = 800000
        self.work_data_path = os.path.join(task.root_path, 'formatting.json')
        self.prompt = self._load_prompt()
        self.model = 'qwen-long'
        # 开始
        self.start()

    def start(self):
        """开始执行

        需要恢复上一次执行断开的地方
        分片后循环送给AI，让AI总结出章节
        根据最后一个章节修正下一个分片点
        """

        # 恢复
        self._recover()

        # 未完成则处理
        if not self.is_complete:
            self._formatting()

        # 输出docx
        save_docx.save(self.task, self.chapters)

    def _recover(self):
        """从上次中断恢复
        """

        # 读取工作数据
        if not os.path.exists(self.work_data_path):
            return

        # 读取保存文件信息
        with open(self.work_data_path, 'r', encoding='utf-8') as json_file:
            work_data = json.load(json_file)
            if work_data is not None:
                self.is_complete = work_data['is_complete']
                self.next_part_pos = work_data['next_part_pos']
                self.chapters = work_data['chapters']
                console.print('recover from %s' % self.next_part_pos)

    def _formatting(self):
        """执行格式化"""

        console.print('formatting...')

        for i in range(self.max_part):
            # 获取分块
            part = self._get_next_part()
            if part is None:
                break
            console.print('pos=%s part=%s whole=%s' % (self.next_part_pos, len(part), len(self.whole_text)))
            # 送给AI，并且更新位置。
            self._handle_part(part)
            # 是否完成
            self.is_complete = len(part) < self.part_size
            # 实时保存
            self._save_work_data()
            # 最后一个part 退出循环
            if self.is_complete:
                break
            # 最大字数
            if self.max_words != 0 and self.next_part_pos >= self.max_words:
                console.print('already to max_words %s ! exit!' % self.max_words)
                break

    def _handle_part(self, part: str):
        """处理分片
        会更新下一个pos
        """
        curr_err = None
        try_count = 3
        while try_count > 0:
            try:
                # 送给AI，拿到章节
                chapters = ask(question=part, system_prompt=self.prompt, model=self.model, rep_format='json')
                for chapter in chapters:
                    if pydash.get(chapter, 'title') is None or pydash.get(chapter, 'content') is None:
                        raise ValueError(f'missing title or content! {chapter}')
                    self.chapters.append(chapter)
                # 更新下一个分块的位置
                self._update_next_pos(part, chapters[-1])
                curr_err = None
                break
            except Exception as e:
                curr_err = e
                console.print('error, retry %s' % try_count)
            try_count -= 1
        # 最后一次还是报错了
        if curr_err is not None:
            raise curr_err

    def _load_prompt(self) -> str:
        curr = os.path.dirname(__file__)
        with open(os.path.join(curr, 'prompt.txt'), 'r', encoding='utf-8') as f:
            return f.read()

    def _update_next_pos(self, part, chapter):
        """查找下一个pos
        根据最后的章节,分片太小会导致bug，每一个分片必须分数多个章节才行！
        """
        find_str = chapter['content'][0:20]
        pos = self._fuzzy_match_str(part, find_str)
        # 找不到
        if pos == -1:
            console.print({
                "title": chapter['title'],
                "content": chapter['content'],
                "part": part,
            })
            raise Exception('cannot find pos in chapter。find_str: \n %s' % find_str)
        # 等于当前，说明卡住了
        if pos == 0:
            raise Exception('next pos fall into a cycle!')
        # 更新下一个分片pos，等同于最后一个章节
        self.next_part_pos += pos

    def _fuzzy_match_str(self, text, pattern, threshold=70):
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

    def _get_next_part(self):
        if self.next_part_pos >= len(self.whole_text):
            return None
        text = self.whole_text[self.next_part_pos:self.next_part_pos + self.part_size]
        return text

    def _get_whole_text(self) -> str:
        """获取完整的文本
        只添加空格，不添加任何其他标点符号
        """
        # 打开并读取 JSON 文件
        texts = []
        with open(self.task.asr_json_path, 'r', encoding='utf-8') as file:
            parts = json.load(file)
            for part in parts:
                texts.append(part['text'])
        return " ".join(texts)

    def _save_work_data(self):
        """保存工作数据"""
        work_data = {
            "next_part_pos": self.next_part_pos,  # 永远都是最新的，下次恢复可直接使用
            "is_complete": self.is_complete,
            "wholeLength": len(self.whole_text),
            "chapters": self.chapters
        }
        with open(self.work_data_path, 'w', encoding='utf-8') as json_file:
            json.dump(work_data, json_file, indent=4, ensure_ascii=False)
