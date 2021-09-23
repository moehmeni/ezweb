import re
from typing import List, Union
from bs4.element import Tag
from trafilatura import extract
from unidecode import unidecode
from cached_property import cached_property
from ezweb.objects import EzSoup
from ezweb.utils.http import soup_from_url
from ezweb.utils.text import clean_title, similarity_of


class EzProduct(EzSoup):
    def __init__(self, url: str) -> None:
        soup = str(soup_from_url(url))
        super().__init__(soup, url=url)
        self.url = url

    @cached_property
    def units(self):
        return ["تومان", "ریال", "$"]

    @cached_property
    def possibility(self):
        max_p = 1.0
        min_p = 0.0
        p = 0.0
        if self.specs:
            p += 0.1
            sl = len(self.specs)
            if sl > 3:
                p += 0.2
            elif sl > 7:
                p += 0.35
        if self.images_src and len(self.images_src) > 3:
            p += 0.15
        if self.price_number:
            p += 0.2
        up1 = self.url_parts[1]
        up2 = self.url_parts[2]
        if up1 and up1.lower() == "product":
            p += 0.6
        if up2 and up2.lower() == "product":
            p += 0.6
        if self.second_title:
            p += 0.35
        if "Product" in self.helper.from_structured_data("@type"):
            p += 0.75
        if p > max_p:
            p = max_p
        if p < min_p:
            p = min_p
        return float(p)

    @cached_property
    def is_product(self):
        return self.possibility >= 0.75

    @cached_property
    def low_price(self):
        """
        returns the lowest price if any discount
        or multiple seller option is provided
        """
        return self.helper.from_structured_data("lowPrice", single=True)

    @cached_property
    def has_discount(self):
        return bool(self.low_price)

    @cached_property
    def availablity(self):
        in_schema = "InStock"
        sd = self.helper.from_structured_data("availability", single=True)
        if not sd:
            return None
        return True if in_schema in sd else False

    @cached_property
    def brand(self):
        b = self.helper.application_json.get("brand")
        if not b:
            return
        if isinstance(b, str):
            return b
        return b.get("name")

    @cached_property
    def structured_id(self):
        sku = self.helper.from_structured_data("sku", single=True)
        mpn = self.helper.from_structured_data("mpn", single=True)
        return sku or mpn

    @cached_property
    def main_text(self):
        return extract(self.content)

    @cached_property
    def short_description(self):
        return self.helper.from_structured_data("description") or self.meta_description

    @cached_property
    def second_title(self):
        sc_title = self.helper.from_structured_data("alternateName")
        if sc_title and isinstance(sc_title, str):
            return clean_title(sc_title, self.site_name)
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

        result = clean_title(el.text, self.site_name)
        # check sim again since even the sorted list el can be a bad value
        sim = similarity_of(result, title)
        if sim > 95 or sim < 49:
            return None

        return result

    @cached_property
    def structured_price(self):
        price = self.helper.from_structured_data("price" , single=True) or self.low_price
        return price

    @cached_property
    def meta_price(self):
        return self.helper.meta_content("property", "product:price:amount")

    @cached_property
    def price_number(self):
        soup_possible_price, unit = self.price_number_unit
        price = self.structured_price or self.meta_price or soup_possible_price
        if not price:
            return None
        if "." in str(price):
            return float(price)
        price = "".join(e for e in unidecode(str(price)) if e.isdigit())
        price = int(price)
        return price

    @cached_property
    def price_unit(self):
        from_sd = self.helper.from_structured_data("priceCurrency", single=True)
        from_ui = self.price_number_unit[1]
        unit = from_sd or from_ui
        return unit

    @cached_property
    def price_number_humanize(self):
        if not self.price_number:
            return None
        return "{:20,.0f}".format(self.price_number).strip()

    @cached_property
    def price(self):
        return {
            "number": self.price_number,
            "unit": self.price_unit,
            "number_humanize": self.price_number_humanize,
            "humanize": f"{self.price_number_humanize} {self.price_unit}",
        }

    @cached_property
    def _price_regex(self):
        string = "\d{1,3}(?:[.,/]\d+)*(?:[.,/]\d+)"
        return re.compile(string, re.UNICODE)

    @cached_property
    def _phone_number_regex(self):
        string = "(\d{2,4}-\d{3,}|[09]\d{7,})"
        return re.compile(string, re.UNICODE)

    @cached_property
    def price_number_unit(self):
        _none = (None, None)
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

        sorted_for_price = sorted(resources, key=lambda t: _price_tag_criterion(t))
        if not sorted_for_price:
            return _none
        tag_with_price_format = sorted_for_price[-1]
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
        return _none

    @cached_property
    def provider_info(self):
        return {
            "name": self.site_name,
            "domain_root": self.root_domain,
            "domain_body": self.site_name_from_host,
            "addresses": self.addresses,
            "phone": self.phones,
        }

    @cached_property
    def addresses(self):
        return self.helper.addresses

    @cached_property
    def phones(self):
        a_tels = self.helper.contains("a", "href", "tel:")
        if a_tels:
            return list({t["href"].split(":")[-1] for t in a_tels})
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

    @cached_property
    def image(self):
        return self.images[0]

    @cached_property
    def images(self):
        def is_sim_to_main_img(img: Tag):
            src = img.get("src", img.get("data-src"))
            sim = similarity_of(self.main_image_src, src)
            return 85 <= sim < 101

        all_imgs = self.helper.all("img", attrs={"src": True})
        images = list(filter(is_sim_to_main_img, all_imgs))

        if not images or len(images) == 1:
            els = self.helper.all_contains("class", "gallery")
            imgs = []
            for el in els:
                if el.name == "img":
                    imgs.append(el)
                imgs.extend(el.find_all("img"))
            images.extend(
                self.helper.from_structured_data("image")
                or imgs
                or self.card.find_all("img")
            )

        return self._ok_images(images)

    @cached_property
    def images_src(self):
        if not self.images:
            return [self.main_image_src]
        srcs = {self.helper.absolute_href_of(i) for i in self.images}
        return sorted(list(srcs))

    @cached_property
    def specs_from_text(self):
        return self._spec_text_to_json(self.main_text)

    @cached_property
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

        high_score_count = len(list(filter(lambda x: x >= 15, product_related_scores)))
        if not high_score_count:
            print("checking the low-level containers for the card...", end=" ")
            product_related_scores.clear()
            els = c("class", "container") + c("class", "row")
            most_content_product_el = sorted(els, key=lambda t: main_card_criterion(t))[
                -1
            ]
            high_score_count = len(
                list(filter(lambda x: x >= 15, product_related_scores))
            )
            if high_score_count:
                print(f"now seems {high_score_count} element(s) have/has a good score")
            else:
                print("couldn't find a main card tag again !")

        return most_content_product_el

    @cached_property
    def specs(self):
        return self.specs_from_text + self.helper.table_info

    @cached_property
    def summary_obj(self):
        obj = {
            "provider": self.provider_info,
            "url": self.url,
            "id_sku_or_mpn": self.structured_id,
            "title": self.title,
            "second_title": self.second_title,
            "availability": self.availablity,
            "low_price": self.low_price,
            "has_discount": self.has_discount,
            "price": self.price,
            "brand": self.brand,
            "images": self.images_src,
            "specs": self.specs,
            "possible_topics": self.possible_topic_names,
            # "links" : self.a_tag_hrefs_internal
            # "card": self._tag_obj(self.card),
            # "main_text" : main_text ,
        }
        return obj

    def _ok_images(self, images: List[Tag]):
        def _ok(i: Tag):
            if not i:
                return
            src = self.helper.absolute_href_of(i)
            if not src:
                return
            _format = "jpg" in src or "png" in src
            not_data = "data:image" not in src
            return src and _format and not_data

        return [i for i in images if _ok(i)]

    def _tag_obj(self, t: Tag):
        return {"tag": t.name, "class": t.get("class", None), "id": t.get("id", None)}

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

        for key, value in matched:
            key = key.replace("-", "").strip()
            value = value.strip()
            if len(key) > 35:  # a long key isn't a good specification
                break
            if key == value:
                break
            d = {key: value}
            if not d:
                break
            result.append(d)

        return result