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
        self.batch_size = 30  # 大于20会导致AI输出错误，即结果数量与句子数量对不上，也会ask函数卡住
        self.max_words = 50000  # 本次最大字数
        self.asr = []
        self.asr_json_path = task.asr_json_path
        self.work_data_path = os.path.join(task.root_path, 'intent.json')
        self.work_data = {
            "is_complete": False,
            "asr_intent_map": {},
            "intent_groups": {}  # { "父意图": "子意图" }
        }

        # 模型
        # 价格核算 max太贵 plus能接受
        self.model = 'qwen-plus'

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
            already = len(self.work_data['asr_intent_map'])
            total = len(self.asr)
            console.print(f'already process {already}, total {total} ')

        # 已完成则退出
        if self.work_data['is_complete']:
            print('already complete!')
            return
        # 递归处理
        self._process()
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
                    self.work_data = {**self.work_data, **work_data}
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
        all_intent = self.work_data['asr_intent_map'].values()
        return list(set(filter(None, all_intent)))

    def _process(self):
        """处理
        不停的循环，直到没有为被处理的句子
        """
        words_count = 0
        while len(self.work_data['asr_intent_map']) < len(self.asr):
            batch = {}
            for i, item in enumerate(self.asr):
                key = f"s{i}"
                if key not in self.work_data['asr_intent_map'] and len(batch) < self.batch_size:
                    words_count += len(item['text'])
                    batch[key] = item["text"]

            if not batch:
                break

            if words_count >= self.max_words:
                raise Exception('max words!')

            # 进度显示
            curr_len = len(self.work_data['asr_intent_map'])
            total = len(self.asr)
            print(f'process {curr_len} / {total}')

            prompt_file = os.path.join(os.path.dirname(__file__), 'intent_pmt.txt')
            prompt = load_prompt(prompt_file, {
                "%sentences%": json.dumps(batch, ensure_ascii=False, indent=4),
                "%intent_library%": ",".join(self._get_all_intents()),
                "%sentence_size%": str(len(batch)),
            })

            # print(prompt)
            # if process_count >= 2:
            #     exit()

            # 调用llm，有最大重试
            for attempt in range(3):
                try:
                    result = ask(prompt, model=self.model, rep_format='json')
                    if not isinstance(result, dict):
                        raise ValueError("resp not dict!")
                    # 对结果进行空值处理，LLM会把null当字符串
                    for key in result:
                        if result[key] == 'null':
                            result[key] = None
                    # 保存
                    self.work_data['asr_intent_map'].update(result)
                    self._persist_work_data('save')
                    break
                except Exception as e:
                    print(str(e))
                    if attempt == 2:
                        raise Exception('max try!')

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
                "%intent_list%": json.dumps(keys, indent=4, ensure_ascii=False),
                "%intent_size%": str(len(keys)),
            })

        # ask llm
        try_count = 2
        last_error = None
        intent_groups = None
        while try_count > 0:
            try:
                resp = ask(get_prompt(), model=self.model, rep_format='json', timeout=10)
                # 必须是字典 {'intent': 'group']
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
        for index in range(len(self.asr)):
            key = f"s{index}"
            item = self.asr[index]
            item['intent'] = self.work_data['asr_intent_map'][key]
            data['asr'].append(item)

        with open(data_file, 'w', encoding='utf-8') as file:
            file.write('setData(' + json.dumps(data, indent=4, ensure_ascii=False) + ')')
