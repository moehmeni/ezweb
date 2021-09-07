from collections import Counter
from rapidfuzz.fuzz import ratio


def similarity_of(str1 :str , str2 : str):
    return round(ratio(str1 , str2))

def list_counter(items: list) -> list:
    _dict = dict(Counter(items))
    result = sorted(_dict.items(), key=lambda x: x[1], reverse=True)
    return result

def clean_title(string : str):
    if not string : return
    bads = ["-", "|", ",", "،"]
    for w in bads:
        string.replace(w, "")
    result = string.strip().replace("\n", "")
    return result