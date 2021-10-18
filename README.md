# EzWeb
 An easy to use web page analyzer (scraper or crawler) with many useful features and properties
 
## Installation
```
pip install ezweb
```
## Basic Usage
```python
from ezweb import EzSoup

url = "https://www.pcmag.com/opinions/windows-11-is-ultra-secure-dont-mess-it-up"

page = EzSoup.from_url(url)

print(page.json_summary)
```
Output :
```json
{
    "url": "https://www.pcmag.com/opinions/windows-11-is-ultra-secure-dont-mess-it-up",
    "source": {
        "url": "https://www.pcmag.com",
        "name": "PCMAG",
        "image": "https://pcmag.com/images/android-chrome-192x192.png",
        "sitemap_url": "https://www.pcmag.com/sitemap-index.xml",
        "articles_count": 43098 // You can also get the all article URLs!
    },
    "title": "Windows 11 Is Ultra SecureDon't Mess It Up",
    "description": "You can’t run Windows 11 on a PC that lacks essential security hardware. That's a good thing. Less promising is the fact that you can disable these requirements. Don't do that!",
    "date": "2021-10-18 00:00:00",
    "main_image": "https://i.pcmag.com/imagery/articles/06Sjyzm7AIuyEF1z9NpXvST-5.1634158671.fit_lim.size_1200x630.jpg",
    "main_content": "Asked why he robbed banks, the notorious Willie Sutton allegedly answered, “Because that’s where the ... [MORE]",
    "possible_topics": [
        "Opinions",
        "Operating systems",
        "Windows"
    ],
    "comments": ""
}
```


## Available properties and methods
 ```python
 # You can use any of below properties and methods instead `a_tags_mp3`
 page.a_tags_mp3
 ```
<details>

<summary>Click to expand!</summary>


#### <kbd>property</kbd> a_tag_hrefs





---

#### <kbd>property</kbd> a_tag_texts





---

#### <kbd>property</kbd> a_tags_mp3





---

#### <kbd>property</kbd> a_tags_rar





---

#### <kbd>property</kbd> a_tags_with_href





---

#### <kbd>property</kbd> article_tag

returns an article tag which has the most text length 

---

#### <kbd>property</kbd> children

returns a list of `EzSoup` instances from `self.important_hrefs` ##### using `ThreadPoolExecutor` to crawl children much faster than normal `for` loop 

---

#### <kbd>property</kbd> favicon_href





---

#### <kbd>property</kbd> important_a_tags

returns `a` tags that includes header (h2, h3) inside or `a` tags inside headers or elements with class `item` or `post` I call these important becuase they're most likely to be crawlable contentful webpages 

---

#### <kbd>property</kbd> important_hrefs





---

#### <kbd>property</kbd> json_summary





---

#### <kbd>property</kbd> main_html





---

#### <kbd>property</kbd> main_image_src





---

#### <kbd>property</kbd> main_text





---

#### <kbd>property</kbd> meta_article_modified_time





---

#### <kbd>property</kbd> meta_article_published_time





---

#### <kbd>property</kbd> meta_description





---

#### <kbd>property</kbd> meta_image_src





---

#### <kbd>property</kbd> possible_topic_names

returns possible topic/breadcrump names of webpage ### values can be unreliable since they aren't generated with NLP methods yet . 

---

#### <kbd>property</kbd> summary_dict





---

#### <kbd>property</kbd> text





---

#### <kbd>property</kbd> title

usually the `<h1>` tag content of a web page is cleaner than original page `<title>` text so if the h1 or h2 text is similar to the title  it is better to return it instead of original title text 

---

#### <kbd>property</kbd> title_tag_text







---

### <kbd>method</kbd> `from_url`

```python
from_url(url: str)
```





---

### <kbd>method</kbd> `get_important_children_soups`

```python
get_important_children_soups(multithread: bool = True, limit: int = None)
```

returns a list of `EzSoup` instances from `self.important_hrefs`  ## Parameters : 
--- `multithread` : True by default , using `ThreadPoolExecutor` to crawl children much faster 
--- `limit`: limit children count that will be crawled 

---

### <kbd>method</kbd> `save_content_summary_html`

```python
save_content_summary_html(path: str = None)
```





---

### <kbd>method</kbd> `save_content_summary_json`

```python
save_content_summary_json(path: str = None)
```





---

### <kbd>method</kbd> `save_content_summary_txt`

```python
save_content_summary_txt(path: str = None)
```

</details>

---

<sub>
This README.md was automatically generated via https://github.com/ml-tooling/lazydocs
</sub>

