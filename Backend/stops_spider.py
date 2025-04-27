import scrapy

class StopsSpider(scrapy.Spider):
    name = 'stops'
    custom_settings = {
        'LOG_ENABLED': True,
        'LOG_LEVEL': 'DEBUG'
    }

    def __init__(self, service_url='', **kwargs):
        super().__init__(**kwargs)
        self.service_url = service_url  # This is needed for start_requests()
        self.start_urls = [service_url]

    def start_requests(self):
        yield scrapy.Request(
            url=self.service_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            },
            callback=self.parse
        )

    def parse(self, response):
        self.logger.info(f"Scraping stops from: {response.url}")
        table = response.css('table.timetable')
        if not table:
            self.logger.warning("No timetable tables found.")
            return

        for stop in table[0].css('tr th.stop-name'):
            name = stop.css('a::text').get()
            if name:
                self.logger.debug(f"Found stop: {name}")
                yield {"name": name}
