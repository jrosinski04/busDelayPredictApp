import uvicorn
import crochet
import asyncio
import traceback
import joblib
import pandas as pd
import holidays
import requests
from crochet import setup, wait_for
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Body
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
db = client["BusDelayPredict"]
services_db = db["servicesBN"]
journeys_db = db["journeysBN"]
model = joblib.load("delay_predictor_lgbm.pkl")
uk_holidays = holidays.UK(subdiv="ENG")

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
    services = services_db.find(
    {
        "$or": [
            {"number": {"$regex":query, "$options": "i"}},
            {"description": {"$regex":query, "$options": "i"}},
        ]
    },
    {})

    results = list(services)
    return results

@app.post("/get_closest_journey")
def get_closest_journey(req: PredictRequest):

    # Parsing date and time
    date = datetime.fromisoformat(req.date).date()
    hr, mins = map(int, req.time.split(":"))
    dep_mins = hr * 60 + mins

    # Establishing time range
    window = 30
    low = dep_mins - window
    high = dep_mins + window

    # Building filter for MongoDB
    filter = {
        "service_id": req.service_id,
        "stop_name": req.stop_name,
        "destination": req.destination,
        "scheduled_mins": {"$gte": low, "$lte": high},
        "is_holiday": date in uk_holidays,
        "is_peak": is_peak(dep_mins, date.weekday()),
    }
    
    # Query and specifying the attributes to return
    retrieved_journeys = list(journeys_db.find(filter, {
        "_id": 0,
        "delay_mins": 1,
        "scheduled_mins": 1,
        "actual_mins": 1,
        "journey_id": 1
    }))

    if not retrieved_journeys:
        raise HTTPException(404, "No matching history found")
    
    # Find closest journey
    closest = min(
        retrieved_journeys,
        key=lambda doc: abs(doc["scheduled_mins"] - dep_mins)
    )
    return closest

def time_to_minutes(timestr: str) -> int:
    h, m = map(int, timestr.split(":"))
    return h * 60 + m

def is_peak(mins: int, weekday: int) -> bool:
    if weekday >= 5: return False
    return (420 <= mins < 540) or (900 <= mins < 1080)

@app.post("/predict_delay")
def predict_delay(req: PredictRequest):

    # Getting the closest scheduled journey to the user's selected time
    closest_j = get_closest_journey(req)
    if not closest_j:
        raise HTTPException(404, "No historical journey found in window")
    
    
    # Getting route info
    svc = services_db.find_one({"_id": req.service_id})
    if not svc:
        raise HTTPException(404, f"Service {req.service_id} not found.")
    
    # Splitting route description into origin and destination
    if "description" not in svc:
        raise HTTPException(500, "Service description missing origin/destination")
    origin, destination = [p.strip() for p in svc["description"].split("-")]

    # Looking up stop index
    sample = journeys_db.find_one(
        {"service_id": req.service_id, "stop_name": req.stop_name},
        {"stop_index": 1}
    )
    if not sample:
        raise HTTPException(404, f"Stop {req.stop_name!r} not found on service.")
    stop_idx = sample["stop_index"]

    # Parsing time and date
    try:
        j_date = datetime.fromisoformat(req.date).date()
        sched_mins = time_to_minutes(req.time)
    except Exception as e:
        raise HTTPException(400, f"Invalid date/time format: {e}")
    
    day_of_week = j_date.weekday()
    peak = is_peak(sched_mins, day_of_week)

    # Assembling feature row
    row = {
        "scheduled_mins": closest_j["scheduled_mins"],
        "day_of_week": [day_of_week],
        "is_peak": [peak],
        "stop_index": [stop_idx],
        "service_id": [req.service_id],
        "stop_name": [req.stop_name],
        "origin": [origin],
        "destination": [destination],
    }

    X = pd.DataFrame(row)

    # Model prediction
    try:
        prediction = model.predict(X)[0]
    except Exception as e:
        raise HTTPException(500, f"Model failed to run: {e}")

    return {"predicted_delay_mins": int(prediction)}    

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

@app.get("/get_stops_api")
def get_stops_basic(service_id: int):
    # Getting journey details
    resp = requests.get(f"https://bustimes.org/api/vehiclejourneys/?service={service_id}", params={"page_size": 100}, timeout=10)
    resp.raise_for_status()
    journeys = resp.json().get("results")

    # Get service details
    resp = requests.get(f"http://bustimes.org/api/services/{service_id}", params={"page_size": 1}, timeout = 10)
    resp.raise_for_status()
    svc = resp.json()
    destination = svc["description"].split("-")[-1].lstrip()


    if not journeys or not svc:
        return {"stops": []}
    
    journey_index = 0
    while (True):
        if journey_index > 5:
            return {"stops": []}

        journey = journeys[journey_index]
        journey_id = journey["id"]

        stops_resp = requests.get(
            f"https://bustimes.org/api/vehiclejourneys/{journey_id}", timeout=10
        )
        stops_resp.raise_for_status()
        stops = [ stop["stop"]["name"] for stop in stops_resp.json().get("times", []) if stop.get("stop").get("name")]

        if destination in stops[-1]:
            break
        journey_index += 1
 
    return stops


@app.get("/get_stops")
def get_stops(service_id: int):
    # Get journey details
    resp = requests.get("https://bustimes.org/api/vehiclejourneys/", params={"service": service_id, "page_size": 1}, timeout=10)
    resp.raise_for_status()
    journeys = resp.json().get("results") or []

    # Get service details
    resp = requests.get(f"http://bustimes.org/api/services/{service_id}", params={"page_size": 1}, timeout = 10)
    resp.raise_for_status()
    svc = resp.json()
    destination = svc["description"].split("-")[-1].lstrip()

    if not journeys or not svc:
        return {"stops": []}
    
    journey_index = 0
    while (True):
        if journey_index > 5:
            return {"stops": []}

        journey = journeys[journey_index]
        journey_id = journey["id"]

        stops_resp = requests.get(
            f"https://bustimes.org/services/{service_id}/journeys/{journey_id}.json", timeout=10
        )
        stops_resp.raise_for_status()

        stops = [ stop["name"] for stop in stops_resp.json().get("stops", []) if stop.get("name")]

        if destination in stops[-1]:
            break
        journey_index += 1
 
    return stops

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)