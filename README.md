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
## Documentation
Soon...