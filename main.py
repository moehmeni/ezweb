from enum import unique
import time, json, datetime
from utils import is_url_root, url_spliter, list_counter
import crawl_utils
from text_process_utils import TextSimilarity
from concurrent.futures import ThreadPoolExecutor

URL = "https://www.zoomg.ir/"
URL_PAGE = "https://www.zoomit.ir/howto/372640-web-searches-secure-private/"
URL_PAGE_2 = "https://digiato.com/article/2021/07/14/%d8%a8%d8%b1%d8%b1%d8%b3%db%8c-%d9%84%d9%be%d8%aa%d8%a7%d9%be-%d8%a7%d9%85-%d8%a7%d8%b3-%d8%a2%db%8c-%d9%85%d8%af%d8%b1%d9%86-%db%b1%db%b4-%d9%85%d8%af%d9%84-a10m/"


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
        links = crawl_utils.all_links_of(soup, root_url=url)
        title = soup.title.string
        title_h1 = soup.find("h1").text.strip() if soup.find("h1") else None

        crawl_time_in_seconds = round(time.time() - t1, 3)

        self.title = title
        self.ready_title = title.split("-")[0].strip()
        self.title_h1 = title_h1
        self.url = url
        self.links = links
        self.just_links = [link["href"] for link in self.links]
        self.crawl_time_seconds = crawl_time_in_seconds
        self.is_first_site_page = is_first_site_page
        self.soup = soup
        self.crawled_date = datetime.datetime.now()
        self._children = []
        self.children_crawl_time_seconds = None

    def most_repeated_paths(self, length: int = 5):
        second_url_children = [
            url_spliter(url)[0] for url in self.just_links if len(url_spliter(url)) > 0
        ]
        return list_counter(second_url_children)[:length]

    def get_all_images(self, key: str = None):
        _all = self.soup.find_all("img")
        custom = None
        if key != None:
            custom = [img[key] for img in _all if img.get(key, "").strip() != ""]
        return custom or _all

    def get_article_element(self):
        el = self.soup.find("article")
        # assert el is not None, "This page hasn't any <article> tag"
        return el

    def article_content(self):
        el = self.get_article_element()
        text = el.text.strip() if el else None
        return text

    def get_article_image_element(self):
        all_images = self.get_all_images()
        ts = TextSimilarity()
        for img in all_images:
            img_alt = img.get("alt", "").strip()
            _title = self.title_h1 or self.ready_title
            is_similar, similarity = ts.is_similar_to(img_alt, _title)
            self.img_alt_similarity_with_title = similarity * 100
            if img_alt != "" and is_similar:
                return img
        return None

    def save_article_locally(self):
        with open(self.title + ".txt", mode="w", encoding="utf-8") as f:
            f.write(self.article_content())

    def is_article_page(self) -> bool:
        page_article_element = self.get_article_element()
        if page_article_element is None:
            return False
        article_content_length_is_enough = len(page_article_element.text) >= 350
        return article_content_length_is_enough

    def crawl_children(self, multithread: bool = True, limit: int = None):
        t1 = time.time()
        _links = self.just_links if not limit else self.just_links[0:limit]
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
        main_img = self.get_article_image_element()
        main_img_src = main_img["src"] if main_img else None
        _dict = {
            "url": self.url,
            "title": self.ready_title,
            "title_h1": self.title_h1,
            "links_count": len(self.just_links),
            "img": [main_img_src] if main_img_src else None,
            "is_root_page": self.is_first_site_page,
            "is_article_page": self.is_article_page(),
            "crawl_time_seconds": self.crawl_time_seconds,
            "crawled_date": self.crawled_date,
            "img_alt_similarity_with_title": self.img_alt_similarity_with_title
            # "article_content": self.article_content(),
        }
        return json.dumps(_dict, indent=4, default=str)


p = WebPage(url=URL)
for page in p.children(multithread=True, limit=5):
    print(page.json())

print("-------\n")
print(p.children_crawl_time_seconds)
