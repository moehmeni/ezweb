from typing import List
from bs4 import BeautifulSoup
from bs4.element import Tag
from trafilatura import extract


class EzSoupHelper:
    def __init__(self, soup: BeautifulSoup) -> None:
        self.soup = soup

    @property
    def summary(self):
        result = extract(self.soup.markup , include_comments=False, include_tables=False, no_fallback=True)
        return result

    @property
    def possible_topics_tags(self) -> List[Tag]:

        id_bread = self.all_contains("id", "breadcrumb")
        class_bread = self.all_contains("class", "breadcrumb")
        class_cat = self.contains("div", "class", "cat")
        class_tag = self.contains("div", "class", "tag")

        maybe_elements = id_bread + class_bread + class_cat + class_tag
        article_ul_tag = self.first("article").find("ul")

        return maybe_elements + article_ul_tag

    @property
    def topics(self):
        return [t.get_text(strip=True) for t in self.possible_topics_tags]

    def all(self, tag_name: str, **kwargs):
        return self.soup.find_all(tag_name, **kwargs)

    def first(self, tag_name: str, *args, **kwargs):
        return self.soup.find(tag_name, *args, **kwargs)

    def xpath(self, pattern: str):
        return self.soup.select(pattern)

    def all_contains(self, attr: str, value: str):
        return self.contains("*", attr, value)

    def meta(self, property):
        return self.first("meta", {"property": property})

    def contains(self, tag_name: str, attr: str, value: str):
        """
        ## Example :
        ```python
        # xpath query will be `div[class*="myClass"]` which means
        # it returns all `div` elements that their class contains 'myClass'
        # for example : `div.hello-myClass` , `div.myClassExample` ...

        elements = contains("div" , "class" , "myClass")

        ```

        ---
        you can use any HTML tag with it's own attributes

        """
        return self.xpath(f'{tag_name}[{attr}*="{value}"]')

    def linked_files(self, extension: str):
        """
        returns all `<a>` tags that their `href` contains `.extension`

        ## Example :

        ```python
        # all a tags that points to a mp3 file
        a_tags = linked_files("mp3")
        ```

        """
        return self.contains("a", "href", f".{extension}")

    @staticmethod
    def absolute_href_of(a_tag: Tag, root_url: str) -> str:
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