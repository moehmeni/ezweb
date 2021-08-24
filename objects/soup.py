import json
from typing import Union
from dateutil.parser import parse as date_parse
from trafilatura import extract
from readability import Document
from concurrent.futures import ThreadPoolExecutor
#
from ezweb.utils.http import safe_get, soup_of
from ezweb.utils.text import similarity_of
from ezweb.utils.souphelper import EzSoupHelper


class EzSoup:
    def __init__(self, content: Union[str, bytes]) -> None:
        self.content = content
        self.soup = soup_of(self.content)
        self.helper = EzSoupHelper(self.soup)

    @staticmethod
    def from_url(url: str):
        return EzSoup(safe_get(url).content)

    @property
    def title_tag_text(self):
        return self.helper.first("title").text.split("-")[0]

    @property
    def text(self):
        return self.soup.get_text(separator="\n", strip=True)

    @property
    def main_text(self):
        result = extract(self.content, include_tables=False , include_comments=False , no_fallback=True)
        return result

    @property
    def main_html(self):
        doc = Document(self.content)
        return doc.summary()

    @property
    def meta_description(self):
        normal = self.helper.meta_content("name" , "description")
        og = self.helper.meta_og_content("description")
        return normal or og

    @property
    def meta_image_src(self):
        return self.helper.meta_og_content("image")

    @property
    def meta_article_published_time(self):
        try :
            time = self.helper.meta_content("property" , "article:published_time")
            return date_parse(time)
        except Exception as e :
            return None

    @property
    def meta_article_modified_time(self):
        try :
            time = self.helper.meta_content("property" , "article:modified_time")
            return date_parse(time)
        except Exception as e :
            return None

    @property
    def main_image_src(self):
        # TODO: Also add article main image to the result
        result = self.meta_image_src
        return result

    @property
    def article_tag(self):
        """
        returns an article tag which has the most text length
        """
        return sorted(self.helper.all("article"), key=lambda tag: len(tag.text))[-1]

    @property
    def a_tags_with_href(self):
        return self.helper.all("a", href=True)

    @property
    def a_tag_texts(self):
        return [a.text for a in self.helper.all("a") if a.text]

    @property
    def a_tag_hrefs(self):
        return [a["href"] for a in self.a_tags_with_href]

    @property
    def a_tags_mp3(self):
        return self.helper.linked_files("mp3")

    @property
    def a_tags_rar(self):
        return self.helper.linked_files("rar")

    @property
    def favicon_href(self):
        icon_links = self.helper.contains("link", "rel", "icon")
        if not icon_links:
            return None

        multiple_sized_icon_links = [
            link for link in icon_links if link.get("sizes", None)]
        if not multiple_sized_icon_links:
            # return the only one src
            return icon_links[0].get("href", None)

        # sort links with their icon image sizes
        sorted_sized_icon_links = sorted(
            multiple_sized_icon_links, key=lambda t: int(t["sizes"].split("x")[0]))
        biggest_icon_link_tag = sorted_sized_icon_links[-1]

        return biggest_icon_link_tag.get("href", None)

    @property
    def title(self):
        """
        usually the `<h1>` tag content of a web page
        is cleaner than original page `<title>` text
        so if the h1 or h2 text is similar to the title 
        it is better to return it instead of original title text
        """
        h1s = self.helper.all("h1")
        h2s = self.helper.all("h2")
        headers = h1s or h2s
        page_title = self.title_tag_text
        for header in headers:
            header_tag_text = header.text.strip() if header and header.text else None
            if header_tag_text is not None:
                # getting the similarity of h1 and original title
                # using `rapidfuzz` library (fuzz.ratio)
                if similarity_of(header_tag_text, page_title) >= 70:
                    return header.text

        # default : return the first h1 tag text or original page title text
        if h1s :
            return h1s[0].get_text(strip=True)
        else :
            return page_title

    @property
    def important_a_tags(self):
        """
        returns `a` tags that includes header (h2, h3) inside
        or `a` tags inside headers or elements with class `item` or `post`
        I call these important becuase they're most likely to be
        crawlable contentful webpages
        """
        a_tags_with_headere_child = [a for a in self.helper.all(
            "a") if a.find("h2") or a.find("h3")]

        headers = self.helper.all("h2") + self.helper.all("h3")

        maybes = self.helper.all_contains("class", "item") + \
            self.helper.all_contains("class", "post")

        all = a_tags_with_headere_child + headers + maybes
        results = []

        for element in all:
            # element itself can be <a>
            # but if it is not it is div , h2 or h3
            # so find the first <a> inside it
            if element.get("href", None) or element.find("a").get("href", None):
                results.append(element)
        return results

    @property
    def important_hrefs(self):
        return [a["href"] for a in self.important_a_tags]

    @property
    def possible_topic_names(self):
        """
        returns possible topic/breadcrump names of webpage
        ### values can be unreliable since they aren't generated with NLP methods yet .
        """
        return self.helper.possible_topic_names

    @property
    def json_summary(self):
        obj = {
            "title": self.title,
            "description" : self.meta_description ,
            "main_image" : self.main_image_src,
            "main_content": self.main_text[:100] +" ...",
            "possible_topics" : self.possible_topic_names,
        }
        return json.dumps(obj, indent=4)

    @property
    def children(self):
        """
        returns a list of `EzSoup` instances from `self.important_hrefs`
        ##### using `ThreadPoolExecutor` to crawl children much faster than normal `for` loop
        """
        return self.get_important_children_soups()

    def get_important_children_soups(self, multithread: bool = True, limit: int = None):
        """
        returns a list of `EzSoup` instances from `self.important_hrefs` 
        ## Parameters :
        ---
        `multithread` :
        True by default , using `ThreadPoolExecutor` to crawl children much faster
        ---
        `limit`:
        limit children count that will be crawled
        """

        links_to_crawl = self.important_hrefs
        links = links_to_crawl[:limit] if limit else links_to_crawl
        if not links:
            return None

        result = []
        if multithread:
            # request children urls with multiple threads
            def maper(url: str):
                result.append(EzSoup.from_url(url))

            with ThreadPoolExecutor() as executor:
                executor.map(maper, links)
        else:
            # normal `for` loop and wait for each request to be completed
            result = [EzSoup.from_url(url) for url in links]

        return result

    def save_content_summary_txt(self, path: str = None):
        _path = path or (self.title + ".txt")
        with open(_path, mode="w", encoding="utf-8") as f:
            f.write(self.summary_text)

    def save_content_summary_html(self, path: str = None):
        _path = path or (self.title + ".html")
        with open(_path, mode="w", encoding="utf-8") as f:
            f.write(self.summary_html)

    def save_content_summary_json(self, path: str = None):
        _path = path or (self.title + ".json")
        with open(_path, mode="w", encoding="utf-8") as f:
            f.write(self.json_summary)
