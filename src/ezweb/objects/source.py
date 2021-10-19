from typing import List, Optional
import feedparser
from feedparser.util import FeedParserDict
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
        return self.rss_data.feed.title

    @cached_property
    def description(self):
        return self.rss_data.feed.description

    @cached_property
    def language(self):
        return self.rss_data.feed.language

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
        possibilities = ["rss", "feed", "feeds"]
        result = None
        for n in possibilities:
            url = self.url
            if url[-1] != "/":
                url += "/"
            url += n
            head = safe_get(url, raise_for_status=False)
            content_type = head.headers.get("content-type", [])
            if head.ok and "rss" in content_type:
                result = url
                break
        assert result, f"Couldn't find a RSS URL for {self.url}"
        # print("Source RSS URL", result)
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
        return feedparser.parse(self.rss_feed_url)

    @cached_property
    def rss_links(self) -> List[str]:
        """Returns the all URLs included in RSS data"""
        return list({i.link for i in self.rss_data.entries})

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
        assert result, f"Couldn't find a Sitemap URL for {self.url}"
        # print("Source Sitemap URL", result)
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

    def get_rss_items(self, ez_soup_class, limit: int = None) -> list:
        """Returns the all `EzSoup` items(articles) provided in the RSS data"""
        result = []
        resource = self.rss_data.entries[:limit] if limit else self.rss_data.entries
        for item in resource:
            tags = [d.get("term") for d in item.get("tags", [])]
            soup = ez_soup_class(url=item.link, topics=tags, source=self)
            result.append(soup)
        return result

    def site_map_links(self, contain: Optional[list]):
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