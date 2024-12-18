import json
import os
from openai import OpenAI
from utils import console

# AI服务
# 使用阿里-通义long
# OpenAI是因为阿里官方的API兼容
apiKey = 'sk-69be04bbadd74475822a9848615d6a14'
apiUrl = 'https://dashscope.aliyuncs.com/compatible-mode/v1'

# 询问AI，单次的，无上下文
def ask(text):
    # 加载提示词
    prompt = loadPrompt()
    # 调用阿里云的
    client = OpenAI(api_key=apiKey,base_url=apiUrl,)
    completion = client.chat.completions.create(
        model="qwen-long",
        messages=[
            {'role': 'system', 'content': prompt},
            {'role': 'user', 'content': text}],
    )
    # 解析结果
    return parseResponse(completion)

# 解析结果
def parseResponse(result):
    # 必须保证有choices结构
    if len(result.choices) == 0:
        raise Exception('No choices found')
    # 解析json
    content = result.choices[0].message.content
    if content.startswith("json "):
        content = content[5:].strip()
    try:
        content = content.strip("'''").strip()
        arr = json.loads(content)
    except Exception as e:
        console.print('*****error***********')
        console.print({
            "err": e,
            "content": content,
        })
        raise Exception('json parse error')
    # ai响应必须是个数组
    if not isinstance(arr, list):
        raise Exception('Invalid response, need list!')
    # 响应的数组每个元素必须包含大户型
    for item in arr:
        # 检查变量是否是字典
        if not isinstance(item, dict):
            raise Exception('item error!')
        # 检查字典是否包含所有指定的键
        requiredKeys = {"title", "content"}
        if not requiredKeys.issubset(item.keys()):
            raise Exception('Required key error!')
    # 返回 [ { title,content,original } ]
    return arr

# 移除代码块
def removeCodeBlock():
    return None

# 加载prompt
def loadPrompt():
    with open('%s/prompt.txt' % os.path.dirname(os.path.abspath(__file__)), 'r', encoding='utf-8') as file:
        prompt = file.read()
    return prompt