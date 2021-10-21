# EzWeb
 An easy to use web page analyzer (scraper or crawler) with many useful features and properties
 
## Installation
```
pip install ezweb
```
## Basic Usage
```python
from ezweb import EzSoup

url = "https://www.theverge.com/22731034/google-pixel-6-pro-price-specs-features-release-date-hands-on"

page = EzSoup(url = url)

print(page.json_summary)
```
Output :
```json
{
    "url": "https://www.theverge.com/22731034/google-pixel-6-pro-price-specs-features-release-date-hands-on",
    "source": {
        "url": "https://www.theverge.com",
        "name": "The Verge",
        "description": "The Verge was founded in 2011 in partnership with Vox Media, and covers the intersection of technology, science, art, and culture. Its mission is to offer in-depth reporting and long-form feature stories, breaking news coverage, product information, and community content in a unified and cohesive manner. The site is powered by Vox Media's Chorus platform, a modern media stack built for web-native news in the 21st century.",
        "language": "en",
        "image": "https://cdn.vox-cdn.com/uploads/chorus_asset/file/7395351/android-chrome-192x192.0.png",
        "rss_feed_url": "https://theverge.com/rss/index.xml",
        "sitemap_url": "https://www.theverge.com/sitemaps"
    },
    "title": "Pixel 6 and 6 Pro: a first look at Google’s shot at a premium Android phone",
    "description": "Google has officially announced its new Pixel 6 and Pixel 6 Pro. The new models start at $599 and $899, respectively, and feature new designs, new cameras, and the first-ever Google custom processor. They are available to preorder starting October 19th and will be shipping on October 28th.",
    "date": "2021-10-19 13:00:00-04:00",
    "main_image": "https://cdn.vox-cdn.com/thumbor/5f5xEVqSF0S3aTCRnoByipEng_4=/0x53:2040x1121/fit-in/1200x630/cdn.vox-cdn.com/uploads/chorus_asset/file/22934833/bfarsace_211014_4802_0013.jpg",
    "main_content": "After many leaks, official teases, and months of waiting, Google has finally given its latest Pixel  ... [MORE]",
    "possible_topics": [
        "Google"
    ],
    "comments": "Loading comments..."
}
```
## Documentation
Soon...