# EzWeb
 An easy to use web page analyzer (scraper or crawler) with many useful features and properties
 
## Installation
```
pip install ezweb
```
## Usage
```python
from ezweb import EzSoup

url = "https://www.techradar.com/reviews/google-pixel-5"

page = EzSoup.from_url(url)

print(page.json_summary)
```
Output :
```json
{
    "title": "Google Pixel 5 review",

    "description": 
    "The Google Pixel 5 sheds a few features to  become a more affordable and compact phone that still takes great photos at a competitive price.",

    "main_image": "https://cdn.mos.cms.futurecdn.net/EicnoxJ3tKYhTRqEauB6RU-1200-80.jpg",

    "main_content":
     "Two-minute review\nThe Google Pixel 5 represents a strategy change for the tech giant: the phone does", // [And more ...]

    "possible_topics": 
    [
        "Mobile Phones",
        "Reviews",
        "Home"
    ]
}
```
