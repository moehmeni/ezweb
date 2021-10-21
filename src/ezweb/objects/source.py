from typing import List, Optional
from urllib.parse import urlparse
import feedparser
from feedparser.util import FeedParserDict
from cached_property import cached_property
import re
from concurrent.futures import ThreadPoolExecutor

# https://stackoverflow.com/questions/28282797/feedparser-parse-ssl-certificate-verify-failed
import ssl
if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context
#

from ezweb.utils.http import (
    can_be_rss_link,
    get_site_map_links,
    name_from_url,
    path_to_url,
    safe_get,
    safe_head,
    soup_from_url,
    url_host,
)
from ezweb.utils.souphelper import EzSoupHelper


    
class EzSource:
    def __init__(self, url: str):
        self.url = "https://" + url_host(url)
        self.soup = soup_from_url(self.url, log_name="EzSource initial")
        self.helper = EzSoupHelper(self.soup, self.url)

    @cached_property
    def name(self):
        return self.helper.site_name or self.name_from_rss or self.name_from_host

    @cached_property
    def name_from_host(self):
        return name_from_url(self.url)

    @cached_property
    def name_from_rss(self):
        return self._from_rss_feed("title")

    @cached_property
    def domain(self):
        """Returns a pattern like `example.com`"""
        return urlparse(self.url).hostname

    @cached_property
    def description(self):
        m = self.helper.meta_content
        return self._from_rss_feed("description") or m("name", "description")

    @cached_property
    def language(self):
        return self._from_rss_feed("language")

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
    def rss_feed_url(self):
        """Returns the possible RSS URL of the source"""
        first_guess = ["rss", "feed", "feeds"]

        def _finder(possibilities: List[str]):
            for url in possibilities:
                response = safe_get(url, raise_for_status=False)
                ct = response.headers.get("content-type", [])
                ct_ok = "xml" in ct or "rss" in ct
                if response.ok and ct_ok:
                    return url
                
        result = _finder([path_to_url(p , self.url) for p in first_guess])
        if not result:
            # find a rss like href in the page
            all_a_tags = self.helper.all("a")
            other_guess = [
                self.helper.absolute_href_of(a)
                for a in all_a_tags
                if can_be_rss_link(a)
            ]
            result = _finder(other_guess)
        return result

    @cached_property
    def rss_data(self) -> FeedParserDict:
        """
        Returns the value of `parse` method of the `feedparser` package.
        return type is : `FeedParserDict`

        ```
        >>> feedparser.parse(self.rss_feed_url)
        ```
        """
        if not self.rss_feed_url:
            return None
        return feedparser.parse(self.rss_feed_url)

    @cached_property
    def rss_links(self) -> List[str]:
        """Returns the all URLs included in RSS data"""
        return list({i.link for i in self.rss_data.get("entries", [])})

    @cached_property
    def site_map_url(self):
        # if sitemap from robots.txt is provided return it
        if self.site_map_url_from_robots_txt:
            return self.site_map_url_from_robots_txt
        possibilities = ["sitemap.xml", "sitemap_index.xml"]
        result = None
        for n in possibilities:
            # lets check which sitemap is a valid sitemap URL
            url = self.url + n
            if safe_head(url, raise_for_status=False).ok:
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
        return self.site_map_links(contain=["article", "blog", "news"])

    @cached_property
    def robots_txt(self):
        url = self.url + "/robots.txt"
        return safe_get(url, log_name="finding sitemap , robot.txt").text

    @cached_property
    def summary_dict(self):
        obj = {
            "url": self.url,
            "name": self.name,
            "description": self.description,
            "language": self.language,
            "image": self.favicon_href,
            "rss_feed_url": self.rss_feed_url,
            "sitemap_url": self.site_map_url,
            # "topics": [],
        }
        return obj

    def _from_rss_feed(self, feedparser_key: str):
        if not self.rss_data:
            return None
        feed = self.rss_data.get("feed")
        if not feed:
            return None
        return feed.get(feedparser_key)

    def get_rss_items(self, ez_soup_class, limit: int = None) -> list:
        """Returns the all `EzSoup` items(articles) provided in the RSS data"""
        if not self.rss_data:
            return []
        entries = self.rss_data.get("entries")
        if not entries:
            return []
        result = []
        resource = entries[:limit] if limit else entries
        for item in resource:
            tags = [d.get("term") for d in item.get("tags", [])]
            soup = ez_soup_class(url=item.link, topics=tags, source=self)
            result.append(soup)
        return result

    def site_map_links(self, contain: Optional[list]):
        if not self.site_map_url:
            return None
        hrefs, directed = get_site_map_links(self.site_map_url, contain=contain)
        if directed:
            return hrefs

        not_xmls = []

        def checker(link: str):
            dot_split = link.split(".")
            if dot_split:
                if dot_split[-1] == "xml":
                    children, directed = get_site_map_links(link)
                    not_xmls.extend(children)
            else:
                not_xmls.append(link)

        with ThreadPoolExecutor() as e:
            e.map(checker, hrefs)

        return list(set(not_xmls))