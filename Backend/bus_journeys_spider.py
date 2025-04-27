import scrapy
import re
import json
from datetime import datetime, timedelta

class BusJourneysSpider(scrapy.Spider):
    name = "bus_journeys"
    custom_settings = {
        "LOG_LEVEL": "DEBUG",
        "DOWNLOAD_DELAY": 0.2,
    }

    def __init__(self, service_link=None, stop_name=None, days=5, **kwargs):
        super().__init__(**kwargs)
        if not service_link or not stop_name:
            raise ValueError("service_link and stop_name are required")
        self.service_link = service_link.rstrip("/")
        self.stop_name = stop_name.strip().lower()
        self.days = days
        self.start_date = datetime.today()
        self.service_id = None

    def start_requests(self):
        # 1) Hit the HTML service page to extract numeric SERVICE_ID
        yield scrapy.Request(self.service_link, callback=self.parse_service_page)

    def parse_service_page(self, response):
        # Look for a <script> tag containing SERVICE_ID = 75684;
        script_text = "".join(response.xpath("//script/text()").getall())
        m = re.search(r"SERVICE_ID\s*=\s*(\d+)", script_text)
        if not m:
            self.logger.error("Couldn't find SERVICE_ID in page scripts!")
            return
        self.service_id = m.group(1)
        self.logger.info(f"Resolved SERVICE_ID = {self.service_id}")

        # 2) Now schedule the last `days` worth of vehicles pages
        for i in range(self.days):
            date = (self.start_date - timedelta(days=i)).strftime("%Y-%m-%d")
            url = f"{self.service_link}/vehicles?date={date}"
            self.logger.debug(f"→ Scheduling vehicles page: {url}")
            yield scrapy.Request(
                url,
                callback=self.parse_vehicles,
                meta={"date": date}
            )

    def parse_vehicles(self, response):
        date = response.meta["date"]
        # Find any links with "#journeys/<id>"
        hrefs = response.css("a[href*='#journeys/']::attr(href)").getall()
        jids = set()
        for href in hrefs:
            m = re.search(r"journeys/(\d+)", href)
            if m:
                jids.add(m.group(1))

        if not jids:
            self.logger.warning(f"No journey IDs found on {response.url}")
            return

        self.logger.info(f"Found {len(jids)} journeys for {date}")
        for jid in jids:
            json_url = (
                f"https://bustimes.org/services/"
                f"{self.service_id}/journeys/{jid}.json"
            )
            self.logger.debug(f"→ Fetching JSON: {json_url}")
            yield scrapy.Request(
                json_url,
                callback=self.parse_journey_json,
                meta={"date": date}
            )

    def parse_journey_json(self, response):
        date = response.meta["date"]
        data = json.loads(response.text)
        stops = data.get("stops", [])
        if not stops:
            self.logger.warning(f"No `stops` array in JSON {response.url}")
            return

        origin      = stops[0]["name"]
        destination = stops[-1]["name"]
        target = None

        for s in stops:
            if s["name"].strip().lower() == self.stop_name:
                target = s
                break

        if not target:
            self.logger.debug(
                f"Stop '{self.stop_name}' not in journey {response.url}"
            )
            return

        yield {
            "date": date,
            "origin": origin,
            "destination": destination,
            "stop": target["name"],
            "scheduled": target.get("aimed_departure_time") or target.get("aimedArrivalTime") or "",
            "actual": target.get("actual_departure_time")   or target.get("actualArrivalTime")  or ""
        }
