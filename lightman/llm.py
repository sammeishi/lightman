"""LLM调用

本模块提供全平台llm的API调用功能。通过部署第三方docker项目one-api实现
可以通过传入不同的模型名实现平台自动切换

接口：
    使用本地部署的new-api/one-api

"""
import os
import re
import json
from openai import OpenAI
import utils

# 默认prompt
def_system_prompt = '你是一个AI助手，完全听从用户的指令，并且能精确的执行用户给出的指令！'


def ask(question: str, model='', system_prompt=def_system_prompt, rep_format='raw'):
    """
    直接询问LLM，没有上下文，单次使用
    :param system_prompt: 系统角色提示词
    :param question: 给LLM的问题
    :param model: 模型名
    :param rep_format: 响应内容格式，取值raw/json
    :return: 模型回答
    """
    msgs = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': question}
    ]
    client = OpenAI(api_key=os.getenv('LLM_API_KEY'), base_url=os.getenv('LLM_API_URL'))
    result = client.chat.completions.create(
        model=model if model else os.getenv('AI_MODEL'),
        messages=msgs
    )
    # 提取到内容
    content = result.choices[0].message.content
    # 转换格式
    if rep_format == 'json':
        return _parse_json_content(content)
    else:
        return content


def check_connect() -> bool:
    return utils.is_url_reachable(os.getenv('LLM_API_URL'))


def _parse_json_content(content: str):
    # 正则表达式匹配Markdown代码块，并提取内容
    pattern = re.compile(
        r'^\s*```(?:json\s*)?([\s\S]+?)```\s*$',
        re.IGNORECASE
    )
    match = pattern.match(content)
    if match:
        extracted = match.group(1).strip()
        content = extracted

    # 尝试解析JSON并返回结果
    return json.loads(content)
