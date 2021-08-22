import time
import datetime
import uuid
from concurrent.futures import ThreadPoolExecutor
# 
from ezweb.objects import EzSoup


class EzPage:
    def __init__(
        self,
        url: str,
    ) -> None:
        self.url = url 
        self.soup = EzSoup.from_url(self.url)
        self.hash = str(uuid.uuid4()).replace("-", "")
        self.crawled_date = datetime.datetime.now()

    # def title_keywords(self):
    #     t = time.time()
    #     title = self.main_h1().text
    #     tagger = POSTagger(model='resources/postagger.model')
    #     tags = tagger.tag(word_tokenize(title))
    #     print(tags)
    #     detect_time_seconds = round(time.time() - t , 3)
    #     print(detect_time_seconds)
    #     allowed = ['N', 'Ne' , 'AJ']
    #     return [t[0] for t in tags if t[1] in allowed] , detect_time_seconds

    def webpages_inside(self, multithread: bool = True, limit: int = None) -> list:
        t1 = time.time()
        def children_crawling_time():
            return round(time.time() - t1, 3)
        links_to_crawl = self.soup.important_hrefs
        links = links_to_crawl[:limit] if limit else links_to_crawl
        if not links:
            return None

        result = []
        if not multithread:
            result = [EzPage(link) for link in links]

        else:

            def maper(url: str):
                return EzPage(url)

            with ThreadPoolExecutor() as executor:
                result = executor.map(maper, links)

        return result

