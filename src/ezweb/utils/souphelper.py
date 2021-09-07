from typing import List, Union
from bs4 import BeautifulSoup
from bs4.element import Tag


class EzSoupHelper:
    def __init__(self, soup: BeautifulSoup) -> None:
        self.soup = soup

    @property
    def site_name(self):
        og_site_name = self.meta_og_content("site_name")
        twitter_meta = self.meta_content("name", "twitter:creator")

        nav = self.first("nav")
        nav_img = nav.find("img", {"alt": True}) if nav else None
        nav_img_alt = nav_img["alt"] if nav_img else None

        text = og_site_name or twitter_meta or nav_img_alt
        if not text:
            return None
        return text.strip()

    @property
    def possible_topic_tags(self) -> List[Tag]:
        """
        returns possible topic/breadcrump tags of webpage
        generated from soup (HTML) itself . 
        """

        id_bread = self.all_contains("id", "breadcrumb")
        class_bread = self.all_contains("class", "breadcrumb")
        class_cat = self.contains("div", "class", "cat")
        class_tag = self.contains("div", "class", "tag")

        maybe_elements_containers = id_bread + class_bread + class_cat + class_tag
        maybe_elements = []

        # filling maybe_elements with all <a> in selected parents (containers)
        for el in maybe_elements_containers:
            a_tags = el.find_all("a")
            if a_tags :
                for a in a_tags :
                    maybe_elements.append(a)

        article_ul_tag = self.first("article").find("ul")
        article_ul_a = article_ul_tag.find_all("a")

        tags = maybe_elements + article_ul_a
        return tags

    @property
    def possible_topic_names(self):
        result = []
        for tag in self.possible_topic_tags :
            text = tag.get_text(strip=True) 
            if text != "" :
                result.append(text)
        return list(set(result))

    def all(self, tag_name: str, **kwargs) -> Union[List[Tag] , None]:
        return self.soup.find_all(tag_name, **kwargs)

    def first(self, tag_name: str, *args, **kwargs):
        return self.soup.find(tag_name, *args, **kwargs)

    def xpath(self, pattern: str):
        return self.soup.select(pattern)

    def all_contains(self, attr: str, value: str):
        return self.contains("*", attr, value)

    def meta(self, key : str , name : str):
        return self.first("meta", {key: name})

    def meta_content(self , key : str , name : str):
        tag = self.meta(key , name)
        if not tag : return None
        return tag.get("content" , None)

    def meta_og_content(self , name : str):
        return self.meta_content("property" , f"og:{name}")

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