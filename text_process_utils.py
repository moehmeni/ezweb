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
