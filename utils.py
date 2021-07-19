from collections import Counter

from bs4.element import Tag
from statistics import mean

URL = "https://www.zoomit.ir/hello/man"
test = ["salam", "hello", "hi", "salam"]


def is_url_root(url: str) -> bool:
    result = True
    if "http" in url:
        try:
            url = url.split("https://")[1]
        except IndexError:
            url = url.split("http://")[1]
        try:
            if not (url.split("/")[1] == ""):
                result = False
        except IndexError as e:
            pass
        return result
    else:
        raise Exception(f"{url} Must be a http/https form")


def url_spliter(url: str, root: bool = False) -> list:
    if "http" in url:
        try:
            url = url.split("https://")[1]
        except IndexError:
            url = url.split("http://")[1]
    root = url.split("/")[0]
    children = url.split("/")[1:]

    result = (root, children) if root == True else children

    return result


def link_of(a_tag: Tag, root_url: str) -> str:
    if a_tag is None : return
    href = a_tag["href"]
    if "http" in href:
        return href
    return root_url + href


def list_counter(items: list) -> list:
    _dict = dict(Counter(items))
    result = sorted(_dict.items(), key=lambda x: x[1], reverse=True)
    return result


def element_with_key(elements: list, key: str):
    custom = None
    if key != None:
        if key == "text":
            custom = [el.text for el in elements if el.text.strip() != ""]
        else:
            custom = [el[key] for el in elements if el.get(key, "").strip() != ""]
    return custom or elements

def topics_ok(topic_names : list) -> bool :
    lens = [len(n) for n in topic_names]
    avg_len = mean(lens)
    return avg_len <= 20