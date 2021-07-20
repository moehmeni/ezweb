from web_crawler.crawl_utils import page_soup
import math, re
from collections import Counter



class TextSimilarity:
    WORD = re.compile(r"\w+")

    def get_cosine(self, vec1, vec2):
        intersection = set(vec1.keys()) & set(vec2.keys())
        numerator = sum([vec1[x] * vec2[x] for x in intersection])

        sum1 = sum([vec1[x] ** 2 for x in list(vec1.keys())])
        sum2 = sum([vec2[x] ** 2 for x in list(vec2.keys())])
        denominator = math.sqrt(sum1) * math.sqrt(sum2)

        if not denominator:
            return 0.0
        else:
            return float(numerator) / denominator

    def text_to_vector(self, text):
        ready_text = re.sub(r"\-|\_|\(|\)|\[|\]|\?|\&|\.", "", text.lower().strip())
        words = self.WORD.findall(ready_text)
        return Counter(words)

    def similarity_of(self, text1, text2):
        vector1 = self.text_to_vector(text1)
        vector2 = self.text_to_vector(text2)
        cosine = self.get_cosine(vector1, vector2)
        return cosine

    def is_similar_to(self, text1: str, text2: str, percentage: int = 70) -> tuple:
        percentage /= 100
        similarity = self.similarity_of(text1, text2)
        return similarity >= percentage, similarity

class AbadisWord:
    _about_url = "https://abadis.ir/?lntype=fatoen,dehkhoda,fatofa,moeen,amid,name,wiki,wikiislamic&word={word}&from=ac"
    _similars_url = "https://abadis.ir/AjaxCommand.aspx?Act=GetWords&Word={word}"

    def __init__(self , word : str) -> None:
        self.word = word

    def about(self):
        url = self._about_url.format(word=self.word)
        soup = page_soup(url)
        wiki_container = soup.find('div' , id='Wiki')
        if wiki_container is not None and wiki_container.text : return wiki_container.text
        user_comments = soup.find_all('div','CommentText')
        if len(user_comments) > 0 : return '،'.join([c.text for c in user_comments if c.text])
        return None

    def similars(self):
        url = self._similars_url.format(word=self.word)
        result = [AbadisWord(span.text) for span in page_soup(url).find_all('span') if span.text and span.text != self.word]
        return result if len(result) > 0 else None

    def __str__(self) -> str:
        return self.word

    def __repr__(self):
        return self.__str__()