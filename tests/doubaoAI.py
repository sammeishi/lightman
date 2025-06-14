from volcenginesdkarkruntime import Ark

client = Ark(api_key="704c71fc-644b-470a-a543-3f42fc582841",  base_url="https://ark.cn-beijing.volces.com/api/v3")

print("----- standard request -----")
completion = client.chat.completions.create(
    model="ep-20241217220130-mtqbz",
    messages=[
        {"role": "system", "content": "你是豆包，是由字节跳动开发的 AI 人工智能助手"},
        {"role": "user", "content": "常见的十字花科植物有哪些？"},
    ],
)
print(completion.choices[0].message.content)