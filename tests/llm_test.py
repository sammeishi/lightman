import json
import os
import sys
import unittest

# 添加src目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from llm import ask

class LLMTestCase(unittest.TestCase):
    def test_parse_json(self):
        a = ask(question="你好啊",model="qwen-long")
        print(a)