# EzWeb
 An easy to use web scraper (crawler) with many cool features  written in python
 
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

```