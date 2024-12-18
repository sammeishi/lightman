import json
import os
from utils import console
from volcenginesdkarkruntime import Ark

# AI服务
# 实测：豆包不行啊，doubao-pro-128K的模型，与qwen-long对比还是差一截
# 1.速度差。豆包2分钟1000字了qwen是1分钟 2.准确度差，doubao好像无法读全文

baseUrl='https://ark.cn-beijing.volces.com/api/v3'
apiKey = '704c71fc-644b-470a-a543-3f42fc582841'
useModel = 'ep-20241217220130-mtqbz'

# 询问AI，单次的，无上下文
def ask(text):
    # 加载提示词
    prompt = loadPrompt()
    # 架子啊
    client = Ark(api_key=apiKey, base_url=baseUrl)
    completion = client.chat.completions.create(
        model=useModel,
        messages=[
            {'role': 'system', 'content': prompt},
            {'role': 'user', 'content': text}
        ],
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