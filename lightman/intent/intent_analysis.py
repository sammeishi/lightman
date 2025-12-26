import os
import json
import shutil
import random

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
        self.batch_size = 20  # 大于20会导致AI输出错误，即结果数量与句子数量对不上，也会ask函数卡住
        self.asr = []
        self.asr_json_path = task.asr_json_path
        self.work_data_path = os.path.join(task.root_path, 'intent.json')
        self.work_data = {
            "is_complete": False,
            "next_index": 0,
            "asr_intent_map": [],  # ['意图1', '意图2']
            "intent_groups": {}  # { "父意图": "子意图" }
        }
        self.model = 'qwen-max'

        # 读取asr 并分配一个id
        with open(self.task.asr_json_path, 'r', encoding='utf-8') as file:
            self.asr = json.load(file)

        # # 开始
        self.start()

    def start(self):
        """入口
        """

        # 恢复上一次
        if self._persist_work_data('recover'):
            console.print('recover from index %s' % self.work_data['next_index'])
        # 已完成则退出
        if self.work_data['is_complete']:
            print('already complete!')
            return
        # 递归处理
        # self._handle_next()
        # 意图词分组
        print('make intent group')
        self._make_group()
        # 输出web
        self._output_web()
        # 标记完成
        self.work_data['is_complete'] = True
        self._persist_work_data('save')
        print('all done!')

    def _persist_work_data(self, operation):
        """从上次中断恢复
        """

        # 恢复
        if operation == 'recover':
            if not os.path.exists(self.work_data_path):
                return False
            with open(self.work_data_path, 'r', encoding='utf-8') as json_file:
                work_data = json.load(json_file)
                if work_data is not None:
                    self.work_data = work_data
                    return True
                else:
                    return False
        # 更新
        if operation == 'save':
            with open(self.work_data_path, 'w', encoding='utf-8') as json_file:
                json.dump(self.work_data, json_file, indent=4, ensure_ascii=False)

        return True

    def _get_all_intents(self):
        """获取所有意图"""
        all_intent = self.work_data['asr_intent_map']
        return list(set(filter(None, all_intent)))

    def _handle_next(self):
        """执行下一批
        """

        # 判断是否结束
        next_index = self.work_data['next_index']
        if next_index >= len(self.asr):
            return

        # 进度
        print(f'process: {next_index} / {len(self.asr)}')

        # 从asr中取得句子列表
        sentences = self.asr[next_index:(next_index + self.batch_size)]
        if len(sentences) == 0:
            raise Exception('empty sentences')

        # 加载prompt并置入句子列表
        sentences = [item['text'] for item in sentences]
        prompt_file = os.path.join(os.path.dirname(__file__), 'intent_pmt.txt')
        prompt = load_prompt(prompt_file, {
            "%sentences%": json.dumps(sentences, ensure_ascii=False, indent=4),
            "%intent_library%": ",".join(self._get_all_intents()),
            "%sentence_size%": str(len(sentences)),
        })

        # ask llm
        try_count = 2
        last_error = None
        resp = None
        while try_count > 0:
            try:
                resp = ask(prompt, rep_format='json')
                if not isinstance(resp, list) or len(resp) != len(sentences):
                    raise Exception(f'resp not list or size wrong! %s' % resp)
                last_error = None
                break
            except Exception as e:
                last_error = e
            try_count = try_count - 1
        if last_error is not None:
            raise Exception(str(last_error))

        # 更新意图表
        self.work_data['asr_intent_map'].extend(resp)

        # 指针更新
        next_index = next_index + len(sentences)
        self.work_data['next_index'] = next_index

        # 保存进度
        self._persist_work_data('save')

        # 递归继续
        self._handle_next()

    def _make_group(self):
        """对意图词分组
        """
        keys = self._get_all_intents()
        if len(keys) == 0:
            raise Exception('empty keys')

        # 获取prompt，会打乱顺序防止缓存
        def get_prompt():
            random.shuffle(keys)
            prompt_file = os.path.join(os.path.dirname(__file__), 'group_pmt.txt')
            return load_prompt(prompt_file, {
                "%intent_list%": json.dumps(keys, indent=4, ensure_ascii=False),  # ",".join(keys),
                "%intent_size%": str(len(keys)),
            })

        # ask llm
        try_count = 3
        last_error = None
        resp = None
        intent_groups = None
        while try_count > 0:
            try:
                resp = ask(get_prompt(), rep_format='json')
                # 必须是字典
                if not isinstance(resp, dict):
                    raise Exception(f'resp not dict %s' % resp)
                # 挨个遍历是否存在
                missing_keys = []
                for key in keys:
                    if key not in resp:
                        missing_keys.append(key)
                if len(missing_keys) != 0:
                    raise Exception(f'missing keys {missing_keys}')
                # 生成分组
                intent_groups = {}
                for subIntent, rootIntent in resp.items():
                    if rootIntent not in intent_groups:
                        intent_groups[rootIntent] = []
                    intent_groups[rootIntent].append(subIntent)
                # 正常执行完，跳出
                last_error = None
                break
            except Exception as e:
                last_error = e
            try_count = try_count - 1
        # 循环完还有错,则异常
        if last_error is not None:
            raise Exception(str(last_error))

        # 保存
        self.work_data['intent_groups'] = intent_groups
        self._persist_work_data('save')

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
        data = {"asr": [], "intent_groups": self.work_data['intent_groups']}

        # 生成asr表，包含意图的
        asr_intent_map = self.work_data['asr_intent_map']
        for index in range(len(self.asr)):
            item = self.asr[index]
            item['intent'] = asr_intent_map[index]
            data['asr'].append(item)

        with open(data_file, 'w', encoding='utf-8') as file:
            file.write('setData(' + json.dumps(data, indent=4, ensure_ascii=False) + ')')

