from collections import Counter
from bs4 import BeautifulSoup
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
        raise Exception(f"{url} Must be an http/https pattern")


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
    if not isinstance(a_tag, Tag):
        raise TypeError(
            f"First argument has to be a Tag instance , [{str(a_tag)}] is {str(type(a_tag))}"
        )
    if a_tag is None:
        return
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
            custom = set([tag_text(el) for el in elements if tag_text_ok(el)])
        else:
            custom = [el[key] for el in elements if el.get(key, "").strip() != ""]
    return custom or elements


def topics_ok(topic_names: list) -> bool:
    if not topic_names:
        return False
    lens = [len(n) for n in topic_names]
    avg_len = mean(lens)
    return avg_len <= 20


def tag_text(t: Tag):
    text = (t.text or t.get("title", None)).strip().replace("\n", "")
    text = " ".join(text.split())
    return text


def tag_text_ok(t: Tag):
    text = tag_text(t)
    ok = text and text != ""
    return ok


def page_name(soup: BeautifulSoup) -> str:
    meta_og_site_name = soup.find("meta", {"property": "og:site_name"})
    if (meta_og_site_name is not None) and (
        meta_og_site_name.get("content", None) is not None
    ):
        return meta_og_site_name["content"]

    title = soup.title.text
    splited = (
        title.split("-")
        if "-" in title
        else title.split("|")
        if "|" in title
        else title.split(":")
        if ":" in title
        else title.split("،")
    )
    name = splited[1] if len(splited) >= 2 else "منبع"
    return name