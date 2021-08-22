from statistics import mean
from collections import Counter
from rapidfuzz.fuzz import ratio


def similarity_of(str1 :str , str2 : str):
    return round(ratio(str1 , str2))

def list_counter(items: list) -> list:
    _dict = dict(Counter(items))
    result = sorted(_dict.items(), key=lambda x: x[1], reverse=True)
    return result

def topics_ok(topic_names: list) -> bool:
    if not topic_names:
        return False
    lens = [len(n) for n in topic_names]
    avg_len = mean(lens)
    return avg_len <= 20

