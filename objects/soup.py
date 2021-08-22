import json
from typing import Union
from dateutil.parser import parse
#
from ezweb.utils.http import safe_get, soup_of
from ezweb.utils.text import similarity_of
from ezweb.utils.souphelper import EzSoupHelper


class EzSoup:
    def __init__(self, content: Union[str, bytes]) -> None:
        self.soup = soup_of(content)
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
    def meta_description(self):
        return self.helper.meta("description").get("content", None)

    @property
    def meta_image(self):
        return self.helper.meta("og:image").get("content", None)

    @property
    def meta_article_published_time(self):
        meta = self.helper.meta("article:published_time")
        if not meta:
            return None
        return parse(meta["content"])

    @property
    def meta_article_modified_time(self):
        meta = self.helper.meta("article:modified_time")
        if not meta:
            return None
        return parse(meta["content"])

    @property
    def display_image_src(self):
        image = self.meta_image
        return image["src"]

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
    def mp3_a_tags(self):
        return self.helper.linked_files("mp3")

    @property
    def rar_a_tags(self):
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
        return h1s[0].text if h1s[0] else page_title

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
    def json_summary(self):
        obj = {
            "title": self.title,
            "content": self.helper.summary,
        }
        return json.dumps(obj, indent=4, sort_keys=True)

    def save_content_summary_json(self, path: str = None):
        _path = path or (self.title + ".json")
        with open(_path, mode="w", encoding="utf-8") as f:
            f.write(self.json_summary)
