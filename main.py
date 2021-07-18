from enum import unique
import time, json, datetime, uuid
from utils import is_url_root, url_spliter, list_counter, element_with_key
import crawl_utils
from text_process_utils import TextSimilarity
from concurrent.futures import ThreadPoolExecutor

URL = "https://www.zoomg.ir/"
URL_PAGE = "https://vigiato.net/p/197937"
URL_WITH_VIDEO = "https://www.zoomg.ir/game-articles/330159-xbox-series-x-games-spec-release-date-buy/"


class WebPage:
    def __init__(
        self,
        url: str,
        # crawl_pages : bool = False
    ) -> None:
        is_first_site_page = False

        if is_url_root(url):
            is_first_site_page = True

        t1 = time.time()
        print(f"Crawling {url}")

        response = crawl_utils.safe_get(url)
        soup = crawl_utils.page_soup(response)
        title = soup.title.string
        meta_tag_description = (
            soup.find("meta", {"name": "description"})["content"].strip()
            if soup.find("meta", {"name": "description"})
            else None
        )
        crawl_time_in_seconds = round(time.time() - t1, 3)

        self.id = str(uuid.uuid4()).replace("-", "")
        self.title = title
        self.meta_tag_description = meta_tag_description
        self.ready_title = title.split("-")[0].strip()
        self.url = url
        self.crawl_time_seconds = crawl_time_in_seconds
        self.is_first_site_page = is_first_site_page
        self.soup = soup
        self.crawled_date = datetime.datetime.now()
        self._children = []
        self.children_crawl_time_seconds = None

    def links(self):
        links = crawl_utils.all_links_of(self.soup, root_url=self.url)
        return links

    def just_links(self, limit: int = None):
        all_links = self.links() if limit is None else self.links()[0:limit]
        links = [link["href"] for link in all_links]
        return links

    def most_repeated_paths(self, length: int = 5):
        second_url_children = [
            url_spliter(url)[0]
            for url in self.just_links()
            if len(url_spliter(url)) > 0
        ]
        return list_counter(second_url_children)[:length]

    def all_images(self, key: str = None):
        _all = self.soup.find_all("img")
        return element_with_key(_all, key)

    def all_videos(self, key: str = None):
        _all = self.soup.find_all("video")
        return element_with_key(_all, key)

    def article_element(self):
        el = self.soup.find("article")
        # assert el is not None, "This page hasn't any <article> tag"
        return el

    def article_content(self):
        el = self.article_element()
        text = el.text.strip() if el else None
        return text

    def main_h1(self):
        all_h1 = self.soup.find_all("h1")
        ts = TextSimilarity()
        for h1 in all_h1:
            h1_text = h1.text.strip() if h1 and h1.text else None
            if h1_text is not None:
                _title = self.ready_title
                is_similar, similarity = ts.is_similar_to(h1_text, _title)
                self.h1_similarity_with_title = round(similarity * 100)
                if is_similar:
                    return h1
        return None

    def article_main_image(self):
        meta_og_img = self.soup.find("meta", {"property": "og:image"})
        if meta_og_img is not None:
            return meta_og_img
        
        all_images = self.all_images()
        ts = TextSimilarity()
        for img in all_images:
            img_alt = img.get("alt", "").strip()
            _title = self.main_h1().text if self.main_h1() else None or self.ready_title
            is_similar, similarity = ts.is_similar_to(img_alt, _title)
            self.img_alt_similarity_with_title = round(similarity * 100)
            if img_alt != "" and is_similar:
                return img

        return self.article_images()[0] if len(self.article_images()) > 0 else None

    def main_img_src(self):
        img = self.article_main_image()
        return img.get("src", img.get("content", ""))

    def article_images(self, key: str = None):
        article = self.article_element()
        _all = article.find_all("img")
        return element_with_key(_all, key)

    def article_headlines(self, key: str = None):
        article = self.article_element()
        _all = article.find_all("h2")
        return element_with_key(_all, key)

    def save_article_locally(self):
        with open(self.title + ".txt", mode="w", encoding="utf-8") as f:
            f.write(self.article_content())

    def is_article_page(self) -> bool:
        page_article_element = self.article_element()
        if page_article_element is None:
            return False
        article_content_length_is_enough = len(page_article_element.text) >= 350
        return article_content_length_is_enough
    
    def page_root_name_fa(self):
        meta_og_site_name = self.soup.find("meta", {"property": "og:site_name"})
        if (meta_og_site_name is not None) and (
            meta_og_site_name.get("content", None) is not None
        ):
            return meta_og_site_name["content"]

        title = self.title
        splited = title.split("-") if "-" in title else title.split("|") if "|" in title else title.split(":")  if ":" in title else title.split("،")
        name = splited[1] if len(splited) >= 2 else None
        return name

    def crawl_children(self, multithread: bool = True, limit: int = None):
        t1 = time.time()
        _links = self.just_links(limit=limit)
        if not multithread:
            self._children = [WebPage(link) for link in _links]
        else:

            def maper(url: str):
                page = WebPage(url)
                self._children.append(page)

            with ThreadPoolExecutor() as executor:
                executor.map(maper, _links)
        self.children_crawl_time_seconds = round(time.time() - t1, 3)

    def children(self, multithread: bool = True, limit: int = None) -> list:
        self.crawl_children(multithread=multithread, limit=limit)
        return self._children

    def json(self):
        main_img = self.article_main_image()
        main_img_src = main_img["src"] if main_img else None
        _dict = {
            "id": self.id,
            "url": self.url,
            "title": self.ready_title,
            "title_h1": self.main_h1().text,
            "links_count": len(self.just_links()),
            "img": [main_img_src] if main_img_src else None,
            "videos": self.all_videos(key="src"),
            "is_root_page": self.is_first_site_page,
            "is_article_page": self.is_article_page(),
            "article_headlines": self.article_headlines(key="text"),
            "article_images": self.article_images(key="src"),
            "crawl_time_seconds": self.crawl_time_seconds,
            "crawled_date": self.crawled_date,
            "img_alt_similarity_with_title": self.img_alt_similarity_with_title,
            "meta_tag_desc": self.meta_tag_description
            # "article_content": self.article_content(),
        }
        return json.dumps(_dict, indent=4, default=str)


p = WebPage(url=URL_PAGE)
print(p.main_img_src())