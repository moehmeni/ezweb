from collections import Counter
from rapidfuzz.fuzz import ratio


def similarity_of(str1 :str , str2 : str):
    return round(ratio(str1 , str2))

def list_counter(items: list) -> list:
    _dict = dict(Counter(items))
    result = sorted(_dict.items(), key=lambda x: x[1], reverse=True)
    return result

def clean_title(string : str , site_name : str = None):
    if not string : return None
    if isinstance(string , str):
        bads = ["-", "|", ",", "،"]
        if site_name:
            bads.append(site_name)
        result = string.strip().replace("\n", "")
        for w in bads:
            string = string.replace(w, "")
        result = string.replace("  " , "").strip()
        if result == "" : return None
        return result

def clean_text(string: str):
    if not string : return None
    if isinstance(string , str):
        text = string.strip().replace("\n", "").replace("\r", "").replace("\t", "")
        if text == "":
            return None
        return text