from requests import Response

class RequestBadStatusCode(Exception):
    def __init__(self, url : str, response : Response):
        self.url = url
        self.response = response
    def __str__(self):
        return f"{self.response.status_code} for {self.url}"