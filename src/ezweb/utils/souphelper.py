from typing import List, Union
from bs4 import BeautifulSoup
from bs4.element import Tag

from ezweb.utils.text import similarity_of

class EzSoupHelper:
    def __init__(self, soup: BeautifulSoup) -> None:
        self.soup = soup

    @property
    def site_name(self):
        og_site_name = self.meta_og_content("site_name")
        twitter_meta = self.meta_content("name", "twitter:creator")
        
        # also nav > image `alt` can be the site title !
        nav = self.first("nav")
        nav_img = nav.find("img", {"alt": True}) if nav else None
        nav_img_alt = nav_img["alt"] if nav_img else None
        # check nav > img : alt similarity with domain root name
        if nav_img_alt :
            # for non ascii chars
            unicoded = unidecode(nav_img_alt)
            domain_name = name_from_url(self.url)
            if not similarity_of(unicoded , domain_name) >= 15 :
                # not reliable img alt
                nav_img_alt = None

        text = og_site_name or twitter_meta or nav_img_alt
                
        return clean_title(text)

    @property
    def possible_topic_tags(self) -> List[Tag]:
        """
        returns possible topic/breadcrump tags of webpage
        generated from soup (HTML) itself .
        """

        id_bread = self.all_contains("id", "breadcrumb")
        class_bread = self.all_contains("class", "breadcrumb")
        breads = id_bread + class_bread

        class_cat = self.contains("div", "class", "cat")
        class_tag = self.contains("div", "class", "tag")
        class_maybe = class_cat + class_tag

        # avoid using not related tags
        if len(class_maybe) > 7:
            class_maybe = []

        maybe_elements_containers = breads + class_maybe
        maybe_elements = []

        # filling maybe_elements with all <a> in selected parents (containers)
        for el in maybe_elements_containers:
            a_tags = el.find_all("a")
            if a_tags:
                for a in a_tags:
                    maybe_elements.append(a)

        article = self.first("article")
        article_ul_tag = article.find("ul") if article else None
        article_ul_a = article_ul_tag.find_all("a") if article_ul_tag else []

        tags = maybe_elements + article_ul_a
        return tags

    @property
    def possible_topic_names(self):

        result = []
        for tag in self.possible_topic_tags:
            text = tag.get_text(strip=True)
            if self._ok_topic_name(text):
                result.append(text)

        return list(set(result))

    def all(self, tag_name: str, **kwargs) -> Union[List[Tag], None]:
        return self.soup.find_all(tag_name, **kwargs)

    def first(self, tag_name: str, *args, **kwargs):
        return self.soup.find(tag_name, *args, **kwargs)

    def xpath(self, pattern: str):
        return self.soup.select(pattern)

    def all_contains(self, attr: str, value: str):
        return self.contains("*", attr, value)

    def meta(self, key: str, name: str):
        return self.first("meta", {key: name})

    def meta_content(self, key: str, name: str):
        tag = self.meta(key, name)
        if not tag:
            return None
        return tag.get("content", None)

    def meta_og_content(self, name: str):
        return self.meta_content("property", f"og:{name}")

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

    def _ok_topic_name(self, name: str):
        reason = None
        if not name or name == "" or len(name) > 26:
            # print("Null topic name or many charachters")
            return False
        site_name = self.site_name
        msg = f"| name : {name} , site name : {site_name}"
        if name == site_name:
            print(f"Topic name is exactly site name {msg}")
            return False
        sim = similarity_of(name, site_name)
        if sim > 65:
            print(f"Topic name is similar with site name {msg} , similarity : {sim}")
            return False
        return True

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