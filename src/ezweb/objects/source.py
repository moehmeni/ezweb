from typing import Optional
from cached_property import cached_property
import re
from concurrent.futures import ThreadPoolExecutor

#
from ezweb.utils.http import (
    get_site_map_links,
    name_from_url,
    safe_get,
    safe_head,
    soup_from_url,
    url_host,
)
from ezweb.utils.souphelper import EzSoupHelper


class EzSource:
    def __init__(self, url: str):
        self.url = "https://" + url_host(url)
        self.soup = soup_from_url(url)
        self.helper = EzSoupHelper(self.soup, self.url)

    @cached_property
    def name(self):
        return self.helper.site_name or self.name_from_host

    @cached_property
    def name_from_host(self):
        return name_from_url(self.url)

    @cached_property
    def favicon_href(self):
        l = self.helper.absolute_href_of
        # 
        icon_links = self.helper.contains("link", "rel", "icon")
        if not icon_links:
            return None

        multiple_sized_icon_links = [
            link for link in icon_links if link.get("sizes", None)
        ]
        if not multiple_sized_icon_links:
            # return the only one src
            return l(icon_links[0].get("href", None))

        # sort links with their icon image sizes
        sorted_sized_icon_links = sorted(
            multiple_sized_icon_links, key=lambda t: int(t["sizes"].split("x")[0])
        )
        biggest_icon_link_tag = sorted_sized_icon_links[-1]

        return l(biggest_icon_link_tag)

    @cached_property
    def site_map_url(self):
        # if sitemap from robots.txt is provided return it
        if self.site_map_url_from_robots_txt:
            return self.site_map_url_from_robots_txt
        possibles = ["sitemap.xml", "sitemap_index.xml"]
        result = None
        for n in possibles:
            # lets check which sitemap is a valid sitemap URL
            url = self.url + n
            if safe_head(url).ok:
                result = url
                break
        return result

    @cached_property
    def site_map_url_from_robots_txt(self):
        r = re.compile("Sitemap:(.+)")
        url = r.search(self.robots_txt).group(1)
        if not url:
            return None
        if not "https" in url:
            url = "https://" + url.split("://")[1]
        return url.strip()

    @cached_property
    def site_map_product_links(self):
        return self.site_map_links(contain=["product"])

    @cached_property
    def site_map_article_links(self):
        return self.site_map_links(contain=["article", "blog" , "news"])
    
    @cached_property
    def robots_txt(self):
        url = self.url + "/robots.txt"
        return safe_get(url).text

    @cached_property
    def summary_dict(self):
        obj = {
            "url": self.url,
            "name": self.name,
            "image": self.favicon_href,
            "sitemap_url" : self.site_map_url ,
            "articles_count" : len(self.site_map_article_links)
            # "topics": [],
        }
        return obj
    
    def site_map_links(self, contain: Optional[list]):
        hrefs , directed = get_site_map_links(self.site_map_url, contain=contain)
        if directed :
            return hrefs
        
        not_xmls = []
        def checker(link: str):
            dot_split = link.split(".")
            if dot_split:
                if dot_split[-1] == "xml":
                    children , directed = get_site_map_links(link)
                    not_xmls.extend(children)
            else:
                not_xmls.append(link)

        with ThreadPoolExecutor() as e:
            e.map(checker, hrefs)
        
        
        return list(set(not_xmls))