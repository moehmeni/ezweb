from enum import unique
import time, json
from utils import is_url_root, url_spliter, list_counter
import crawl_utils
from text_process_utils import TextSimilarity

URL = "https://www.zoomg.ir/"
URL_PAGE = "https://www.zoomit.ir/howto/372640-web-searches-secure-private/"
URL_PAGE_2 = "https://digiato.com/article/2021/07/14/%d8%a8%d8%b1%d8%b1%d8%b3%db%8c-%d9%84%d9%be%d8%aa%d8%a7%d9%be-%d8%a7%d9%85-%d8%a7%d8%b3-%d8%a2%db%8c-%d9%85%d8%af%d8%b1%d9%86-%db%b1%db%b4-%d9%85%d8%af%d9%84-a10m/"


class WebPage:
    def __init__(
        self,
        url: str,
    ) -> None:
        is_first_site_page = False
        if is_url_root(url):
            is_first_site_page = True

        t1 = time.time()

        response = crawl_utils.safe_get(url)
        soup = crawl_utils.page_soup(response)
        links = crawl_utils.all_links_of(soup, root_url=url)
        title = soup.title.string

        crawl_time_in_seconds = round(time.time() - t1, 3)

        self.title = title
        self.ready_title = title.split("-")[0].strip()
        self.url = url
        self.links = links
        self.just_links = [link["href"] for link in self.links]
        self.crawl_time_seconds = crawl_time_in_seconds
        self.is_first_site_page = is_first_site_page
        self.soup = soup

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
        text = el.text.strip()
        return text

    def get_article_image_element(self):
        all_images = self.get_all_images()
        for img in all_images:
            if (
                img.get("alt", "").strip() != ""
                and TextSimilarity().is_similar_to(img["alt"], self.title)[0]
            ):
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

    def json(self):
        _dict = {
            "title": self.ready_title,
            "url": self.url,
            "img": [self.get_article_image_element()["src"]],
            "is_first_page": self.is_first_site_page,
            "crawl_time_seconds": self.crawl_time_seconds,
            "article_content": self.article_content(),
        }
        return json.dumps(_dict)


p = WebPage(url=URL)
print(p.is_article_page())