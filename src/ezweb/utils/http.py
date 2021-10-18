import requests
from pathlib import PurePosixPath
from typing import Union
from bs4 import BeautifulSoup, FeatureNotFound
from urllib.parse import unquote, urlparse
import os


def cls():
    os.system("cls" if os.name == "nt" else "clear")


def safe_get(url: str) -> requests.Response:
    print(f"Requesting {url}\n", end="\r")
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    t = round(response.elapsed.total_seconds(), 3)
    print(f"> Request finished : {t} seconds")
    return response


def safe_head(url: str) -> requests.Response:
    print(f"Heading {url}\n", end="\r")
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36"
    }
    response = requests.head(url, headers=headers)
    response.raise_for_status()
    t = round(response.elapsed.total_seconds(), 3)
    print(f"> Head Request finished : {t} seconds")
    return response


def soup_from_url(url: str) -> BeautifulSoup:
    response = safe_get(url)
    return soup_of(response.text)


def soup_of(content: Union[str, bytes]):
    try:
        soup = BeautifulSoup(content, features="lxml")
        return soup
    except FeatureNotFound as e:
        soup = BeautifulSoup(content, features="html.parser")
        return soup


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


def pure_url(url: str):
    parsed = urlparse(url).path
    unquoted = unquote(parsed)
    pure = PurePosixPath(unquoted)
    return pure.parts


def url_host(url: str):
    return urlparse(url).hostname


def name_from_url(url: str):
    root = url_host(url)
    if not root:
        return None
    dot_splited = root.split(".")
    name = dot_splited[1] if "www" in root else dot_splited[0]
    return name.capitalize()


def get_site_map_links(url: str, contain: list = None):
    soup = soup_from_url(url)
    hrefs = list({a["href"] for a in soup.find_all("a", href=True)})
    if not hrefs or len(hrefs) < 3:
        locs = soup.find_all("loc")
        if locs:
            hrefs = list({t.get_text(strip=True) for t in locs if t.text})
    if contain:

        def contain_cond(url: str):
            for w in contain:
                w = w.lower()
                parts = pure_url(url)
                if len(parts) >= 2 and w in parts[1].lower():
                    return True
                if len(parts) >= 3 and w in parts[2].lower():
                    return True
            return False

        hrefs = [l for l in hrefs if contain_cond(l)]
    return hrefs