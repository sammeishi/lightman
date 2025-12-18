import os
import json
import shutil

from utils import console
from utils import load_prompt
from models import Task
from llm import ask


class IntentAnalysis:
    """
    意图分析
    使用AI对每一个句子的意图进行分析，统计，输出统计报表
    """

    def __init__(self, task: Task):
        self.task = task
        self.next_index = 0
        self.batch_size = 20
        self.asr = []
        self.asr_json_path = task.asr_json_path
        self.asr_intent_map = {}
        self.is_complete = False
        self.work_data_path = os.path.join(task.root_path, 'intent.json')
        self.model = 'qwen-max'

        # 读取asr 并分配一个id
        with open(self.task.asr_json_path, 'r', encoding='utf-8') as file:
            self.asr = json.load(file)
            id_base = 1
            for item in self.asr:
                item['id'] = "s" + str(id_base)
                id_base = id_base + 1

        # # 开始
        self.start()

    def start(self):
        """入口
        """

        # 恢复上一次
        self._recover()
        # 已完成则退出
        if self.is_complete:
            print('already complete!')
            return
        # 继续处理下一批
        self._handle_next()
        # 输出web
        self._output_web()

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
                self.next_index = work_data['next_index']
                self.asr_intent_map = work_data['asr_intent_map']
                console.print('recover from index %s' % self.next_index)

    def _intent_key_library(self):
        """提取出意图关键词库"""
        keys = []
        for index in self.asr_intent_map:
            keys.append(self.asr_intent_map[index])
        return keys

    def _handle_next(self):
        """执行下一批
        """
        # 进度
        print(f'process: {self.next_index} / {len(self.asr)}')
        # 从asr中取得句子列表
        sentences = self.asr[self.next_index:(self.next_index + self.batch_size)]
        if len(sentences) == 0:
            raise Exception('empty sentences')
        tmp_arr = []
        for item in sentences:
            tmp_arr.append({"id": item['id'], "text": item['text']})
        # 加载prompt并置入句子列表
        prompt_file = os.path.join(os.path.dirname(__file__), 'prompt.txt')
        prompt = load_prompt(prompt_file, {
            "%sentences%": json.dumps(tmp_arr, ensure_ascii=False, indent=4),
            "%intent_key_library%": ",".join(self._intent_key_library())
        })
        # ask llm
        try_count = 3
        last_error = None
        resp = None
        while try_count > 0:
            try:
                resp = ask(prompt, rep_format='json')
                self._verify_resp(resp)
                last_error = None
                break
            except Exception as e:
                last_error = e
            try_count = try_count - 1
        if last_error is not None:
            raise Exception(str(last_error))
        # 指针更新
        self.next_index = self.next_index + len(sentences)
        # 更新意图表
        for item in resp:
            self.asr_intent_map[item['id']] = item['key']
        # 判断是否完成
        if self.next_index >= len(self.asr):
            self.is_complete = True
        # 保存进度
        work_data = {
            "next_index": self.next_index,  # 永远都是最新的，下次恢复可直接使用
            "is_complete": self.is_complete,
            "asr_intent_map": self.asr_intent_map
        }
        with open(self.work_data_path, 'w', encoding='utf-8') as json_file:
            json.dump(work_data, json_file, indent=4, ensure_ascii=False)

        # 递归继续
        if not self.is_complete:
            self._handle_next()

    def _output_web(self):
        """输出web数据
        拷贝web结构性代码
        生成嵌入js的data.js
        """

        # 拷贝web目录
        web_dir = os.path.join(os.path.dirname(__file__), 'web')
        output_dir = os.path.join(self.task.root_path, 'intent_web')
        shutil.copytree(web_dir, output_dir, dirs_exist_ok=True)

        # 生成web用的data文件
        data_file = os.path.join(output_dir, 'data.js')
        data = []
        for item in self.asr:
            itemId = item['id']
            if itemId in self.asr_intent_map:
                key = self.asr_intent_map[itemId]
                item['intention'] = key
            data.append(item)
        with open(data_file, 'w', encoding='utf-8') as file:
            file.write('setData(' + json.dumps(data, indent=4, ensure_ascii=False) + ')')

    def _verify_resp(self, resp):
        """验证返回是否正确
        """
        if not isinstance(resp, list):
            raise Exception('resp not list')
        for item in resp:
            if not isinstance(item, dict):
                return False
            if not all(k in item for k in ['id', 'key']):
                raise Exception('resp item need id and key !')

        return True
