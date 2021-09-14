import re
from typing import List, Union
from bs4.element import Tag
import json
from trafilatura import extract
from unidecode import unidecode
from ezweb.objects import EzSoup
from ezweb.utils.http import soup_from_url
from ezweb.utils.text import clean_title, similarity_of


class EzProduct(EzSoup):
    def __init__(self, url: str) -> None:
        super().__init__(str(soup_from_url(url)))
        self.url = url
        self._main_text_container = None

    @property
    def units(self):
        return ["تومان", "ریال", "$"]

    @property
    def main_text(self):
        if self._main_text_container:
            return self._main_text_container
        result = extract(self.content)
        self._main_text_container = result
        return result

    @property
    def second_title(self):
        json_title = self._json_extract(self.application_json, "alternateName")
        if json_title:
            return clean_title(json_title)
        h1 = self.card.find("h1")
        els = [self.card.find("h2")] + (h1.find_all() if h1 else [])
        els = [i for i in els if i is not None]

        if not els:
            return None

        title = self.title

        def _sec_title_criterion(t: Tag):
            if not t:
                return 0
            text = t.get_text(strip=True)
            if not text:
                return 0
            sim = similarity_of(t.text.strip(), title)
            if sim < 49:
                # it is not similar to main title
                return 0
            if sim > 95:
                # it is main title itself !
                return 0
            return sim

        sorted_with_similarity = sorted(els, key=lambda t: _sec_title_criterion(t))
        el = sorted_with_similarity[-1]

        if not el:
            return None

        result = clean_title(el.text)
        # check sim again since even the sorted list el can be a bad value
        sim = similarity_of(result, title)
        if sim > 95 or sim < 49:
            return None

        return result

    @property
    def application_json(self):
        all_json_tags = self.helper.all("script", attrs={"type": "application/ld+json"})
        tag = sorted(
            all_json_tags, key=lambda t: len(t.contents[0] if t.contents else [])
        )[-1]
        string = tag.contents[0] if tag.contents else None
        result = json.loads(string) if string and string != "" else None
        return result

    @property
    def application_json_price(self):
        if self.application_json:
            prices = self._json_extract(self.application_json, "price")
            if not prices:
                return None
            price = 0
            for p in sorted(prices):
                if p and float(p) != 0:
                    price = p
                    break
            # print(f"-----\n Json price : {price} \n-----")
            return price

    @property
    def meta_price(self):
        return self.helper.meta_content("property", "product:price:amount")

    @property
    def price(self):
        soup_possible_price, unit = self.price_number_unit
        price = self.meta_price or self.application_json_price or soup_possible_price
        if price is None or unit is None:
            return None
        return f"{price} {unit}"

    @property
    def _price_regex(self):
        string = "\d{1,3}(?:[.,/]\d+)*(?:[.,/]\d+)"
        return re.compile(string, re.UNICODE)

    @property
    def _phone_number_regex(self):
        string = "(\d{2,4}-\d{3,}|[09]\d{7,})"
        return re.compile(string, re.UNICODE)

    @property
    def price_number_unit(self):
        helper = self.helper
        resources = helper.all_contains("class", "price") + helper.all_contains(
            "id", "price"
        )

        if not resources:
            resources = helper.all_contains("class", "value")

        def _price_tag_criterion(t: Tag):
            if not t or not t.text or t.text.strip() == "":
                return 0
            return len(re.findall(self._price_regex, unidecode(t.text)))

        tag_with_price_format = sorted(
            resources, key=lambda t: _price_tag_criterion(t)
        )[-1]
        text = tag_with_price_format.get_text(strip=True)

        # tp = self._tag_obj(tag_with_price_format)
        # print(tp)

        for unit in self.units:

            if unit in text:
                # unit found
                # decode for non english digits to make regex work
                for n in "۱۲۳۴۵۶۷۸۹۰" + "١٢٣٤٥٦٧٨٩٠":
                    if n in text:
                        text = unidecode(text)
                        break

                numbers = re.findall(self._price_regex, text)

                if not numbers:
                    tp = self._tag_obj(tag_with_price_format)
                    raise Exception(f"No price format found in text:\n{text}\n{tp}")

                return numbers[-1], unit
        return None, None

    @property
    def provider_info(self):
        return {
            "name": self.site_name,
            "domain_root": self.root_domain,
            "domain_body": self.site_name_from_host,
            "address": self.address,
            "phone": self.phones,
        }

    @property
    def address(self):
        h = self.helper
        tags = (
            h.all_contains("class", "address", parent_tag_name="footer")
            + h.all_contains("class", "location", parent_tag_name="footer")
            + h.all("address")
        )

        if not tags:
            footer = h.all("footer")[-1]
            words = ["شعبه", "پلاک", "خیابان", "بلوار", "میدان"]
            for w in words:
                search = footer.select(f'*:-soup-contains("{w}")')
                if search:
                    tags.extend(search)
                    break

        texts = list({t.text.strip().replace("\n", "") for t in tags if t.text})
        return texts[0] if texts else None

    @property
    def phones(self):
        tags = self.helper.all_contains("class", "phone", parent_tag_name="footer")

        if not tags:
            # search in footer if 'phone' like class isn't in the DOM
            tags = [self.helper.all("footer")[-1]]
            if not tags:
                return []

        numbers = []
        for t in tags:
            nums = self.helper._number_groups(t, pattern=self._phone_number_regex)
            if nums:
                numbers.extend(nums)

        return list(set(numbers))

    @property
    def image(self):
        return self.images[0]

    @property
    def images(self):
        els = self.helper.all_contains("class", "gallery")
        imgs = []
        for el in els:
            if el.name == "img":
                imgs.append(el)
            imgs.extend(el.find_all("img"))
        return self._ok_images(imgs or self.card.find_all("img"))

    @property
    def images_src(self):
        srcs = {self._img_src(i) for i in self.images}
        return list(srcs)

    @property
    def specs(self):
        return self._spec_text_to_json(self.main_text)

    @property
    def card(self) -> Union[Tag, None]:
        class_p = self.helper.all_contains("class", "product")
        id_p = self.helper.all_contains("id", "product")

        els = [tag for tag in class_p + id_p if tag.name != "body"]

        if not els:
            els = self.helper.all_contains("class", "container")

        def main_card_criterion(tag: Tag):
            point = 0
            high_score = tag.name == "article" or tag.find("h1")
            mid_score = len(tag.find_all("h2")) == 1
            if high_score:
                point = point + 30
            if mid_score:
                point = point + 15
            imgs = self._ok_images(tag.find_all("img"))
            score = len(imgs) + point
            # if score > 2 :
            # print(f"{tag.name} class : {tag.get('class' , None)} , id : {tag.get('id' , None)}   score : {score}")
            return score

        most_content_product_el = sorted(els, key=lambda t: main_card_criterion(t))[-1]
        return most_content_product_el

    @property
    def summary_obj(self):
        # with open("card.txt" , "w" , encoding="utf-8") as f :
        #     f.write(str(self.main_text))
        # main_text = self.main_text
        obj = {
            # "card": self._tag_obj(self.card),
            "provider": self.provider_info,
            "title": self.title,
            "second_title": self.second_title,
            "price": self.price,
            "images": self.images_src,
            # "main_text" : main_text ,
            "specs": self.specs,
        }
        return obj

    def _img_src(self, img: Tag):
        return img.get("src", img.get("data-src", None))

    def _ok_images(self, images: List[Tag]):
        def _ok(i: Tag):
            src = self._img_src(i)
            return src and ("jpg" in src or "png" in src)

        return [i for i in images if _ok(i)]

    def _tag_obj(self, t: Tag):
        return {"tag": t.name, "class": t.get("class", None), "id": t.get("id", None)}

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

    def _spec_text_to_json(self, text: str):
        if not text:
            return []

        regex = re.compile("(.*):(.*)")
        matched = re.findall(regex, text)
        result = []

        if not matched:
            splited = text.split("\n")
            keys = []
            values = []
            if splited:
                for index, w in enumerate(splited):
                    if index % 2 == 0:
                        keys.append(w)
                    else:
                        values.append(w)
                matched = list(zip(keys, values))

        for _tuple in matched:
            key, value = _tuple
            key = key.replace("-", "").strip()
            d = {key: value}
            result.append(d)

        return result