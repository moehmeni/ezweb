from typing import List, Optional
from urllib.parse import urlparse
import feedparser
from feedparser.util import FeedParserDict
from cached_property import cached_property
import re
from concurrent.futures import ThreadPoolExecutor

# https://stackoverflow.com/questions/28282797/feedparser-parse-ssl-certificate-verify-failed
import ssl

if hasattr(ssl, "_create_unverified_context"):
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
        hostname = urlparse(self.url).hostname
        if "www." in hostname :
            hostname = hostname.split("www.")[1]
        return hostname

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
    def rss_feed_url_raw_data(self):
        """Returns the possible RSS URL of the source"""
        
        # first try to find a RSS-like href in the page
        all_a_tags = self.helper.all(["a" , "link"])
        guess = [
            self.helper.absolute_href_of(a)
            for a in all_a_tags
            if can_be_rss_link(a)
        ]
        result = self._rss_link_finder(guess)
        
        # if there wasn't , check these paths
        if not result:
            print("RSS URL not found in the page")
            other_guess = ["rss", "feed", "feeds"]
            other_guess = [path_to_url(p, self.url) for p in other_guess]
            result = self._rss_link_finder(other_guess)
            
        return result or (None , None)
    
    @cached_property
    def rss_feed_url(self):
        return self.rss_feed_url_raw_data[0]
    
    @cached_property
    def rss_feed_raw_data(self):
        return self.rss_feed_url_raw_data[1]

    @cached_property
    def rss_data(self) -> FeedParserDict:
        """
        Returns the value of `parse` method of the `feedparser` package.
        return type is : `FeedParserDict`

        ```
        >>> feedparser.parse(self.rss_feed_raw_data)
        ```
        """
        if not (self.rss_feed_url and self.rss_feed_raw_data):
            return None
        return feedparser.parse(self.rss_feed_raw_data)

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

    def get_rss_items(
        self,
        ez_soup_class,
        rss_url: str = None,
        multithread: bool = True,
        limit: int = None,
    ) -> list:
        """Returns the all `EzSoup` items(articles) provided in the RSS data"""
        data = feedparser.parse(rss_url) if rss_url else self.rss_data
        if not data:
            return []
        entries = data.get("entries")
        if not entries:
            return []
        result = []
        resource = entries[:limit] if limit else entries

        def _do(item):
            tags = [d.get("term") for d in item.get("tags", [])]
            soup = ez_soup_class(url=item.link, topics=tags, source=self)
            result.append(soup)

        if multithread:
            with ThreadPoolExecutor() as e:
                e.map(_do, resource)
        else:
            for item in resource:
                _do(item)
        return result
    
    def _rss_link_finder(self , possibilities: List[str]):
        for url in possibilities:
            response = safe_get(url, raise_for_status=False)
            ct = response.headers.get("content-type", [])
            ct_ok = "xml" in ct or "rss" in ct
            if response.ok and ct_ok:
                return url , response.text

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