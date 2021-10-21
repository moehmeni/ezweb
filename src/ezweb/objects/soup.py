from collections import Counter
import json
from typing import List
from bs4.element import Tag
from dateutil.parser import parse as date_parse
import trafilatura
import readability
from concurrent.futures import ThreadPoolExecutor
from cached_property import cached_property

#
from ezweb.utils.http import (
    safe_get,
    soup_of,
    pure_url,
    url_host,
)
from ezweb.utils.text import similarity_of, clean_title
from ezweb.utils.souphelper import EzSoupHelper
from ezweb.objects.source import EzSource
from ezweb.utils.io import create_file


class EzSoup:
    def __init__(
        self,
        content: str = None,
        url: str = None,
        source: EzSource = None,
        topics: List[str] = None,
    ) -> None:
        assert (
            content or url
        ), "At least one of page HTML content or page URL must be determined"
        if not content:
            self.content = safe_get(url, log_name="EzSoup initial").text
        else:
            self.content = content
        if url:
            self.source = source or EzSource(url)

        self.soup = soup_of(self.content)
        self.helper = EzSoupHelper(self.soup, url=url)

        # Initilizing some containers to avoid recalculate -
        # pre-determined arguments
        self.url = url
        self._topics = topics

    @cached_property
    def url_parts(self):
        if self.url:
            return pure_url(self.url)

    @cached_property
    def root_domain(self):
        return url_host(self.url).replace("www.", "")

    @cached_property
    def root_url(self):
        if not self.root_domain:
            return
        return "https://" + self.root_domain

    @cached_property
    def title_tag_text(self):
        tag = self.helper.first("title")
        if not tag:
            return None
        return clean_title(tag.text, self.source.name)

    @cached_property
    def main_text(self):
        return trafilatura.extract(self.content, include_tables=False)

    @cached_property
    def main_text_without_comments(self):
        return trafilatura.extract(
            self.content, include_tables=False, include_comments=False
        )

    @cached_property
    def readablity_document(self) -> readability.Document:
        """Returns `readability.Document` instance of this soup"""
        return readability.Document(self.content)

    @cached_property
    def trafilatura_bare_extract(self):
        """Returns `trafilatura.bare_extraction`output (dict) of this.soup"""
        return trafilatura.bare_extraction(
            self.content, date_extraction_params={"outputformat": "%Y-%m-%dT%H:%M:%S%z"}
        )

    @cached_property
    def comments_text(self):
        return self.trafilatura_bare_extract.get("comments")

    @cached_property
    def main_html(self):
        return self.readablity_document.summary()

    @cached_property
    def last_date(self):
        """Returns the possible last date that this page has been modified"""
        d = self.trafilatura_bare_extract.get("date")
        if not d:
            return
        return date_parse(d)

    @cached_property
    def meta_description(self):
        normal = self.helper.meta_content("name", "description")
        og = self.helper.meta_og_content("description")
        return normal or og

    @cached_property
    def meta_image_src(self):
        return self.helper.meta_og_content("image")

    @cached_property
    def meta_article_published_time(self):
        try:
            time = self.helper.meta_content("property", "article:published_time")
            return date_parse(time)
        except Exception:
            return None

    @cached_property
    def meta_article_modified_time(self):
        try:
            time = self.helper.meta_content("property", "article:modified_time")
            return date_parse(time)
        except Exception:
            return None

    @cached_property
    def main_image_src(self):
        return self.meta_image_src or self.article_tag_image_src

    @cached_property
    def article_tag(self):
        """
        returns an article tag which has the most text length
        """
        articles = self.helper.all("article")
        if not articles:
            return None
        return sorted(articles, key=lambda tag: len(tag.text))[-1]

    @cached_property
    def article_tag_image(self):
        """
        returns the image which has the most similarity
        with the page title
        """
        images = self.article_tag_images
        if not images:
            return None
        return images[0]

    @cached_property
    def article_tag_image_src(self):
        image = self.article_tag_image
        if not image:
            return None
        return image.get("src", None)

    @cached_property
    def a_tags_with_href(self):
        return self.helper.all("a", href=True)

    @cached_property
    def a_tag_texts(self):
        return list({a.text for a in self.helper.all("a") if a.text})

    @cached_property
    def a_tag_hrefs(self):
        return [
            x
            for x in list(
                {self.helper.absolute_href_of(a) for a in self.a_tags_with_href}
            )
            if x
        ]

    @cached_property
    def a_tag_hrefs_internal(self):
        return [
            x
            for x in list(
                {self.helper.absolute_href_of(a, True) for a in self.a_tags_with_href}
            )
            if x
        ]

    @cached_property
    def a_tags_mp3(self):
        return self.helper.linked_files("mp3")

    @cached_property
    def a_tags_rar(self):
        return self.helper.linked_files("rar")

    @cached_property
    def article_tag_images(self):
        def _img_criterion(img: Tag):
            sim = similarity_of(page_title, img.get("alt", "").strip())
            return sim

        images = self.article_tag.find_all("img", {"src": True, "alt": True})
        if not images:
            return []
        page_title = self.title
        # the first image alt has the most similarity with title
        images = sorted(images, key=lambda x: _img_criterion(x), reverse=True)
        return images

    @cached_property
    def is_article(self):
        """
        check the page is a true article page or not
        """
        article_tag = self.article_tag
        if not article_tag or not article_tag.text:
            return False
        if len(article_tag.text.strip()) < 350:
            return False
        date = self.meta_article_published_time or self.meta_article_published_time
        if not date:
            return False
        return True

    @cached_property
    def title(self):
        readability_title = self.readablity_document.short_title()
        return clean_title(readability_title, self.source.name)

    @cached_property
    def _not_important_routes(self):
        return ["search", "cart", "faq", "about-us", "terms", "landings"]

    @cached_property
    def important_a_tags(self):
        """
        returns `a` tags that includes header (h2, h3) inside
        or `a` tags inside headers or elements with class `item` or `post`
        I call these important becuase they're most likely to be
        crawlable contentful webpages
        """
        a_tags_with_header_child = [
            a for a in self.helper.all("a") if a.find("h2") or a.find("h3")
        ]

        headers = self.helper.all("h2") + self.helper.all("h3")
        li_tags = self.helper.all("li")

        maybes = self.helper.all_contains("class", "item") + self.helper.all_contains(
            "class", "post"
        )

        els = [i for i in (a_tags_with_header_child + headers + li_tags + maybes) if i]
        results = []

        # print(f"---\n{len(els)} container found\n---")

        for element in els:
            if not element:
                continue
            if element.name == "a" and (element.get("href", None) is None):
                continue
            # element itself can be <a>
            # but if it is not it is div , h2 or h3
            # so find the first <a> inside it
            element = (
                element
                if element.name == "a"
                else element.find_all("a", {"href": True})
            )
            if element:
                if isinstance(element, list):
                    # it can be a list since we called `find_all` if it's not an <a>
                    results.extend(element)
                else:
                    results.append(element)

        return results

    @cached_property
    def important_hrefs(self):
        links_container = []
        url_part_count_container = []
        for a in self.important_a_tags:
            if a.get("href"):
                # check if first part is in important routes then count it also.
                link = self.helper.absolute_href_of(a)
                if not link:
                    continue
                parts = self.url_parts
                parts_count = len(parts)
                just_one_route = parts_count == 2
                if "/#" in link:
                    continue
                if parts_count > 1 and parts[1] in self._not_important_routes:
                    continue
                if parts_count <= 1:
                    continue
                if just_one_route and "@" in parts[1]:
                    continue
                last_part = parts[-1]
                if len(last_part) < 4:
                    continue

                url_part_count_container.append(parts_count)
                links_container.append(link)

        # for example if 3 is the number just count the urls which has 3 part
        # beacause they're most possible items that can be a main link of the web page
        most_repeated_url_part_number = Counter(url_part_count_container).most_common(
            1
        )[0][0]
        print(
            f"I guess the urls which has {most_repeated_url_part_number} part(s) are the main ones"
        )

        _list = list(set(links_container))

        result = list(
            filter(lambda x: len(pure_url(x)) == most_repeated_url_part_number, _list)
        )

        return result

    @cached_property
    def topic_names(self):
        """
        returns RSS data topics or the possible topic/breadcrumb names of the webpage
        and thus values can be unreliable
        since they aren't generated with the NLP methods.
        """
        return self._topics or self.helper.possible_topic_names

    @cached_property
    def summary_dict(self):
        obj = {
            "source": self.source.summary_dict,
            "title": self.title,
            "description": self.meta_description,
            "date": str(self.last_date),
            "main_image": self.main_image_src,
            "main_content": self.main_text[:100] + " ...",
            "possible_topics": self.topic_names,
            "comments": self.comments_text,
        }
        if self.url:
            obj = {**{"url": self.url}, **obj}
        return obj

    @cached_property
    def json_summary(self):
        return json.dumps(self.summary_dict, indent=4, ensure_ascii=False)

    @cached_property
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
        `multithread` :
        True by default , using `ThreadPoolExecutor` to crawl children much faster

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
                result.append(EzSoup(url=url))

            with ThreadPoolExecutor() as executor:
                executor.map(maper, links)
        else:
            # normal `for` loop and wait for each request to be completed
            result = [EzSoup(url=url) for url in links]

        return result

    def save_content_summary_txt(self, path: str = None, custom_content: str = None):
        path = path or ((self.title or "no-title") + ".txt")
        create_file(path, custom_content or self.main_text)

    def save_content_summary_html(self, path: str = None):
        path = path or (self.title + ".html")
        create_file(path, self.main_html)

    def save_content_summary_json(self, path: str = None, custom_content: str = None):
        path = path or (self.title + ".json")
        create_file(path, custom_content or self.json_summary)

    def save_site_map_links(self, contain: list = None, path: str = None):
        path = path or (self.title + ".txt")
        create_file(path, "\n".join(self.source.site_map_links(contain=contain)))
