# EzWeb
 An easy to use web page analyzer (scraper or crawler) with many useful features and properties

## Quick Access
- [Notes](#notes)
- [Installation](#installation)
- [Basic example](#basic-example)
- [EzProduct](#ezproduct)

## Installation
```
pip install ezweb
```
## Basic Example
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

## EzProduct
```python
from ezweb import EzProduct

url = "https://www.razer.com/gaming-laptops/Razer-Blade-15/RZ09-0409JED3-R3U1"

page = EzProduct(url)

print(page.json_summary)
```
Output:
```json
{
    "provider": {
        "name": "Razer",
        "domain": "razer.com",
        "addresses": null,
        "phone": []
    },
    "url": "https://www.razer.com/gaming-laptops/Razer-Blade-15/RZ09-0409JED3-R3U1",
    "id_sku_or_mpn": null,
    "title": "Blade 15 Advanced Model QHD 240Hz GeForce RTX 3070 Black",
    "second_title": null,
    "is_available": true,
    "low_price": 2699.99,
    "high_price": 2699.99,
    "has_discount": true,
    "discount_percentage": 0,
    "price": {
        "number": 2699.99,
        "unit": "USD",
        "number_humanize": "2,700",
        "humanize": "2,700 USD"
    },
    "brand": "Razer",
    "images": [
        "https://assets3.razerzone.com/BXmAEATSJMaLlom3EfL6iwV0QuU=/1500x1000/https%3A%2F%2Fhybrismediaprod.blob.core.windows.net%2Fsys-master-phoenix-images-container%2Fha6%2Fh11%2F9208511594526%2F500x500-blade15-may2021-fhd.png"
    ],
    "specs": [
        {
            "Processor": "11th Gen Intel® Core™ i7-11800H 8 Cores (2.3GHz / 4.6GHz)"
        },
        {
            "OS": "Windows 11 Home"
        },
        {
            "Display": "15.6\" QHD 240Hz, 100% DCI-P3, G-Sync, 2.5ms, individually factory calibrated"
        },
        {
            "Graphics": "Discrete: NVIDIA® GeForce RTX™3070 (8GB GDDR6 VRAM)Integrated: Intel® UHD Graphics"
        },
        // And more...
    ],
    "possible_topics": []
}
```

## Notes
- `EzSoup` and especially `EzProduct` results are more accurate for Persian websites
- Since I did not spend much time documenting the code, the package structure might look confusing
