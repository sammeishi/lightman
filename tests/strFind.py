from thefuzz import fuzz


def fuzzy_match_thefuzz(text, pattern, threshold=70):
    """查找文本中以指定字符串开头的最佳匹配"""
    best_match = None
    best_similarity = 0

    for i in range(len(text) - len(pattern) + 1):
        # 直接取固定长度的子串
        substring = text[i:i + len(pattern)]

        # 使用ratio()代替partial_ratio()，确保从开头匹配
        similarity = fuzz.ratio(substring, pattern)

        if similarity > best_similarity and similarity >= threshold:
            best_similarity = similarity
            best_match = {
                'position': i,
                'similarity': similarity,
            }
    return best_match['position']


# 示例使用
if __name__ == "__main__":
    text = '''
    阴阳实际上是正气的细分。整个宇宙所有的星球可以分成两类：一类是发光发热的，像太阳；一类是不发光发热的，像地球。具体到一个人身上，无论是男 女都可以分成两部分：后背为阳，前胸为阴。身体的内部又可以分成两类：气为阳，血为阴。中医说的阴阳是正气的细分，人的真阳正气可以分成两个阶段：一个是积累正气，增加正气的过程，叫做阴；另一个是消耗正气，让正气发挥生理功能的过程，叫做阳。
    '''
    pattern = "阴阳实际上是正气的细分。整个宇宙所有的星"

    result = fuzzy_match_thefuzz(text, pattern)
    print(text[result: result+10])