import json
from urllib.parse import urlparse
import re
from typing import List, Union
from bs4 import BeautifulSoup
from bs4.element import Tag
from unidecode import unidecode
from cached_property import cached_property
import itertools

#
from ezweb.utils.http import name_from_url, pure_url
from ezweb.utils.text import clean_text, clean_title, similarity_of


class EzSoupHelper:
    def __init__(self, soup: BeautifulSoup, url: str) -> None:
        self.soup = soup
        self.url = url

    @cached_property
    def site_name(self):
        og_site_name = self.meta_og_content("site_name")
        twitter_meta = self.meta_content("name", "twitter:creator")

        # also nav > image `alt` can be the site title !
        nav = self.first("nav")
        nav_img = nav.find("img", {"alt": True}) if nav else None
        nav_img_alt = nav_img["alt"] if nav_img else None
        # check nav > img : alt similarity with domain root name
        if nav_img_alt:
            # for non ascii chars
            unicoded = unidecode(nav_img_alt)
            domain_name = name_from_url(self.url)
            if not similarity_of(unicoded, domain_name) >= 15:
                # not reliable img alt
                nav_img_alt = None

        text = og_site_name or twitter_meta or nav_img_alt

        return clean_title(text)

    @cached_property
    def possible_topic_tags(self) -> List[Tag]:
        """
        returns possible topic/breadcrump tags of webpage
        generated from soup (HTML) itself .
        """
        # get some nav
        nav = []
        for n in self.all("nav"):
            if 1 < len(n.find_all("a", href=True)) <= 4:
                nav.append(n)

        id_bread = self.all_contains("id", "breadcrumb")
        class_bread = self.all_contains("class", "breadcrumb")
        breads = id_bread + class_bread

        class_cat = self.contains("div", "class", "cat")
        class_tag = self.contains("div", "class", "tag")
        class_label = self.contains("div", "class", "label")
        class_maybe = class_cat + class_tag + class_label
        
        class_maybe_li = []
        for el in class_maybe :
            if el.name == "li":
                class_maybe_li.append(el)
                continue
            lis = el.find_all("li")
            if lis :
                class_maybe_li.extend(lis)

        # avoid using not related tags
        if len(class_maybe) > 6:
            class_maybe = []

        # avoid using not related tags
        for tag in breads:
            bread_a_tags = []
            if tag.name == "a":
                bread_a_tags.append(tag)
            for a in tag.find_all("a"):
                bread_a_tags.append(a)
            if len(bread_a_tags) > 10:
                breads = []

        # print("nav", len(nav), "breads", len(breads), "class_maybe", len(class_maybe))
        
        maybe_elements_containers = nav + breads + class_maybe
        maybe_elements = []
        
        # if li tags are ok , set them
        if 0 < len(class_maybe_li) < 6 :
            maybe_elements_containers = class_maybe_li
            
        # filling maybe_elements with all <a> in selected parents (containers)
        for el in maybe_elements_containers:
            a_tags = el.find_all("a")
            if a_tags:
                for a in a_tags:
                    maybe_elements.append(a)

        article = self.first("article")
        article_ul_tag = article.find("ul") if article else None
        article_ul_a = article_ul_tag.find_all("a") if article_ul_tag else []

        print("maybe", len(maybe_elements), "article_ul", len(article_ul_a))
        tags = maybe_elements + article_ul_a
        return tags

    @cached_property
    def table_info(self):
        tables = self.all("table")
        result = []
        for table in tables:
            if not table:
                continue
            rows = table.find_all("tr")
            if not rows:
                return []
            for row in rows:
                cells = row.find_all("td")
                headers = row.find_all("th")
                if not cells or not headers:
                    break
                for head, cell in zip(headers, cells):
                    ht = self.tag_text(head)
                    ct = self.tag_text(cell)
                    if ht == ct:
                        break
                    d = {ht: ct}
                    if not d:
                        break
                    result.append(d)

        return result

    @cached_property
    def possible_topic_names(self):

        result = []
        for tag in self.possible_topic_tags:
            text = tag.get_text(strip=True)
            if self._ok_topic_name(text):
                result.append(text.capitalize())

        return list(set(result))

    @cached_property
    def addresses(self):
        classes = ["address", "location", "contact"]
        words = [
            "آدرس",
            "نشانی",
            "شعبه",
            "خیابان",
            "کوچه",
            "پلاک",
            "بلوار",
            "میدان",
            "چهارراه",
            "طبقه",
            "تفاطع",
        ]
        #
        def _result(res: list):
            return sorted(res)

        def _texts_of(tags):
            return list({clean_text(t.text) for t in tags if t.text})

        ad_tags = self.all("address")
        if ad_tags:
            texts = _texts_of(ad_tags)
            if texts:
                return _result(texts)

        def _f(class_name):
            """Returns all `class_name` like tags in the footer"""
            return self.all_contains("class", class_name, "footer")

        tags = []
        for c in classes:
            tags.extend(_f(c))

        if tags:
            texts = _texts_of(tags)
            return _result(texts) if texts else []
        else:
            # searching
            footers = self.all("footer")
            if not footers:
                return []
            footer = footers[-1]
            for w in words:
                search = footer.find_all(text=True)
                texts = list(
                    {
                        clean_text(text)
                        for text in search
                        if w in text and len(text) >= 45
                    }
                )
                if texts:
                    return _result(texts)

    @cached_property
    def question_answers(self):
        q_tags_texts = self.all_contains("class", "faq", just_text=True)
        return [self.question_answer_from_text(t) for t in q_tags_texts]
        # return q_tags_texts

    @cached_property
    def _bad_topic_names(self):
        vocab = {
            "fa": ["فروشگاه", "خانه", "صفحه اصلی", "برگشت", "بازگشت"],
            "en": ["home", "return", "back", "undo", "shop", "change"],
        }
        # merge all d values list into one list of str
        result = list(itertools.chain.from_iterable(vocab.values()))
        return result

    @cached_property
    def application_json(self) -> dict:
        all_json_tags = self.all("script", attrs={"type": "application/ld+json"})
        if not all_json_tags:
            return None
        tag = sorted(
            all_json_tags, key=lambda t: len(t.contents[0] if t.contents else [])
        )[-1]
        string = tag.contents[0] if tag.contents else None
        result = json.loads(string) if string and string != "" else None
        return result

    def all(self, tag_name: str, **kwargs) -> Union[List[Tag], None]:
        return self.soup.find_all(tag_name, **kwargs)

    def first(self, tag_name: str, *args, **kwargs):
        return self.soup.find(tag_name, *args, **kwargs)

    def xpath(self, pattern: str):
        return self.soup.select(pattern)

    def all_contains(
        self, attr: str, value: str, parent_tag_name: str = "*", just_text: bool = False
    ):
        res = self.contains(parent_tag_name, attr, value)
        if just_text:
            res = [self.tag_text(t) for t in res if self.tag_text(t)]
        return res

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

    def from_structured_data(
        self, key: str, multiple: bool = False, unique: bool = False
    ):
        """
        Guide : https://developers.google.com/search/docs/advanced/structured-data/intro-structured-data

        Test a URL : https://developers.google.com/search/docs/advanced/structured-data/
        """
        from_json_ld = self.from_json_schema(key)
        # TODO: providing other structured schemas like
        # RDFa and Microdata
        result = from_json_ld
        if unique:
            result = list(set(result))
        if result:
            if multiple:
                return result
            else:
                return result[0]

    def from_json_schema(self, key: str):
        """
        returns a list of the values of `key` param if
        page schema exists and
        the `key` exists in the page schema
        page schema can be application json tag
        """
        json_ld = self._json_extract(self.application_json, key)
        return json_ld

    def _json_extract(self, obj, key):
        """Recursively fetch values from nested JSON."""
        arr = []

        def extract(obj, arr, key):
            """Recursively search for values of key in JSON tree."""
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if isinstance(v, (dict, list)):
                        extract(v, arr, key)
                    elif k == key:
                        arr.append(v)
            elif isinstance(obj, list):
                for item in obj:
                    extract(item, arr, key)
            return arr

        values = extract(obj, arr, key)

        return values

    def _ok_topic_name(self, name: str) -> bool:
        if name.isdigit() : return
        name = name.lower()
        if not name or name == "" or len(name) > 26:
            # print("Null topic name or many charachters")
            return
        ws = ["@:]["]
        for w in ws : 
            if w in name : return
        if name.split()[0] in self._bad_topic_names:
            return
        site_name = self.site_name
        msg = f"| name : {name} , site name : {site_name}"
        if name == site_name:
            # print(f"Topic name is exactly site name {msg}")
            return
        sim = similarity_of(name, site_name)
        if sim > 65:
            # print(f"Topic name is similar with site name {msg} , similarity : {sim}")
            return
        return True

    def _number_groups(self, t: Tag, pattern):
        text = t.text
        if not text:
            return []
        text = text.strip().replace("\n", "").replace(" ", "")
        text = unidecode(text)

        c = []
        nums = re.findall(pattern, text)
        for n in nums:
            if "-" in n:
                first = n.split("-")[0]
                last = n.split("-")[-1]
                if len(first) > len(last):
                    # it has reversed wrong (RTL langs)
                    c.append("".join([last, first]))
                    break
            c.append(n)
        return c

    def tag_text(self, t: Tag):
        if not t or not t.text:
            return None
        return clean_text(t.text)

    def question_answer_from_text(self, text: str):
        regex = re.compile("(.*)[?؟](.*)")
        matches = re.findall(regex, text)

        def _ok(k, v):
            if not k or k.strip().replace("\n", "") == "":
                return False
            if not v or v.strip().replace("\n", "") == "":
                return False
            return True

        return {k.strip(): v.strip() for k, v in matches if _ok(k, v)}

    def absolute_href_of(
        self, source: Union[str, Tag], should_be_internal=False
    ) -> str:
        if not source:
            return
        link = None
        if isinstance(source, Tag):
            if source.name in ["a", "link"] and not ("http" in source):
                link = source.get("href")
            else:
                link = source.get("src", source.get("data-src"))

        if not link:
            return
        
        root_domain = urlparse(self.url).netloc.replace("www.", "")
        root = "https://" + root_domain
        result = None
        if "http" in link:
            result = link
            if should_be_internal:
                # the link is not internal and is for another website
                link_domain = urlparse(link).netloc.replace("www.", "")
                is_internal = link_domain == root_domain
                if not is_internal:
                    return None
                
        elif "www" in link:
            link = link[link.index("www"):]
            link = "/" + "/".join(pure_url(link)[1:])
            result = root + link
            
        else:
            if link[0] != "/":
                # hashtags or ?&
                return None
            result = root + link

        return result