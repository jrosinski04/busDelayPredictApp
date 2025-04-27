import scrapy
from fastapi.middleware.cors import CORSMiddleware

class ServicesSpider(scrapy.Spider):
    name = 'services'

    def __init__(self, query='', **kwargs):
        super().__init__(**kwargs)
        self.start_urls = [f'https://bustimes.org/search?q={query.replace(" ", "+")}']

    def parse(self, response):
        first_service = response.css('ul.has-smalls li a')
        if first_service:
            href = first_service[0].attrib['href']
            yield {
                'link': 'https://bustimes.org' + href
            }
