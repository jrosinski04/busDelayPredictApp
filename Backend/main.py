import uvicorn
import crochet
import asyncio
import traceback
import logging
from crochet import setup, wait_for
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pymongo import MongoClient
from pydantic import BaseModel
from scrapy.crawler import CrawlerRunner
from scrapy.signalmanager import dispatcher
from scrapy.utils.project import get_project_settings
from scrapy import signals

from stops_spider import StopsSpider
from services_spider import ServicesSpider
from bus_journeys_spider import BusJourneysSpider

setup()
app = FastAPI()
client = MongoClient("mongodb+srv://kuba08132004:Solo1998@jrcluster.nwclg.mongodb.net/?retryWrites=true&w=majority&appName=JRCluster")


# Enable CORS (Allow React frontend to access API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

class PredictRequest(BaseModel):
    service_id: int
    stop_name: str
    destination: str
    date: str
    time: str

@app.get("/")
def home():
    return {"message": "FastAPI is running!"}

@app.get("/get_services")
async def get_services(query: str ):
    db = client["BusDelayPredict"]
    collection = db["services"]
    services = collection.find(
    {
        "$or": [
            {"Service": {"$regex":query, "$options": "i"}},
            {"Origin": {"$regex":query, "$options": "i"}},
            {"Destination": {"$regex":query, "$options": "i"}}
        ]
    },
    {"_id": 0})

    results = list(services)
    return results

@app.post("/get_historical_delays")
def get_historical_delays(req: PredictRequest):

    # Parsing date and time
    date = datetime.fromisoformat(req.date).date()
    hr, min = map(int, req.time.split(":"))
    dep_mins = hr * 60 + min

    # Establishing time range
    window = 80
    low = dep_mins - window
    high = dep_mins + window

    # Building filter for MongoDB
    filter = {
        "service_id": req.service_id,
        "stop_name": req.stop_name,
        "destination": req.destination,
        "scheduled_mins": {"$gte": low, "$lte": high},
        "date": req.date
    }
    
    # Query
    col = client.BusDelayPredict.journeysTEST

    docs = list(col.find(filter, {
        "_id": 0,
        "delay_mins": 1,
        "scheduled_mins": 1,
        "actual_mins": 1,
        "journey_id": 1
    }))

    if not docs:
        raise HTTPException(404, "No matching history found")
    
    return docs

result = []

@app.get("/get_service_link")
async def get_service_link(query: str ):
    result.clear()

    run_service_spider(query)

    timeout=10
    while not result and timeout > 0:
        await asyncio.sleep(0.2)
        timeout -= 0.2

    if result:
        return {"link": result[0]['link']}
    else:
        return {"error": "No result found"}


def handle_service(item, response, spider):
    result.append(item)

def run_service_spider(query):
    dispatcher.connect(handle_service, signal=signals.item_passed)
    runner = CrawlerRunner()

    d = runner.crawl(ServicesSpider, query=query)
    return d

# ---- STOP SCRAPER ENDPOINT ----
@app.get("/get_stops")
async def get_stops(serviceURL: str):
    print(f"Received service URL: {serviceURL}")

    @crochet.wait_for(timeout=15.0)
    def run_spider(service_url):
        results = []

        def collect_item(item, response, spider):
            print(f"Collected stop: {item}")
            results.append(item)

        dispatcher.connect(collect_item, signal=signals.item_passed)

        runner = CrawlerRunner()
        d = runner.crawl(StopsSpider, service_url=service_url)

        def cleanup(_):
            print(f"Spider done for URL: {service_url}")
            dispatcher.disconnect(collect_item, signal=signals.item_passed)
            return results

        d.addBoth(cleanup)
        return d

    try:
        scraped_items = await asyncio.to_thread(run_spider, serviceURL)
        stop_names = [item.get("name") for item in scraped_items if item.get("name")]
        print(f"Final scraped stops: {stop_names}")
        return {"stops": stop_names}
    except Exception as e:
        print(f"Error in /get_stops: {e}")
        return {"error": str(e), "stops": []}

# 2) Create a single Runner instance
runner = CrawlerRunner(get_project_settings())

# 3) Define your request body schema
class JourneyRequest(BaseModel):
    service_link: str   # e.g. "https://bustimes.org/services/440-rochdale-syke-2"
    stop_name:   str    # e.g. "Rochdale Interchange"

# 4) Spider‑invoking function (runs in a background thread, blocks until complete)
@wait_for(timeout=120.0)
def run_journey_spider(service_link: str, stop_name: str):
    results = []

    def collect_item(item, response, spider):
        print(f"[crawl] collected item: {item}")
        results.append(item)

    dispatcher.connect(collect_item, signal=signals.item_passed)
    try:
        d = runner.crawl(
            BusJourneysSpider,
            service_link=service_link,
            stop_name=stop_name
        )
        d.addBoth(lambda _: dispatcher.disconnect(collect_item, signal=signals.item_passed))
        d.addCallback(lambda _: results)
        return d
    except Exception as e:
        print("[crawl] exception in run_journey_spider:", e)
        traceback.print_exc()
        raise

@app.post("/get_journey_data")
def get_journey_data(req: JourneyRequest):
    try:
        print(f"[api] Got request: {req}")
        data = run_journey_spider(req.service_link, req.stop_name)
        print(f"[api] Spider returned {len(data)} items")
        return data
    except Exception as e:
        # Log full stack
        print("[api] exception in get_journey_data:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)