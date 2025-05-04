import uvicorn
import joblib # loads machine learning models
import pandas as pd
import numpy as np
import holidays
import requests
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from pydantic import BaseModel

app = FastAPI() # FastAPI setup

# Connecting to and configuring MongoDB collections
client = MongoClient("mongodb+srv://kuba08132004:Solo1998@jrcluster.nwclg.mongodb.net/?retryWrites=true&w=majority&appName=JRCluster")
db = client["BusDelayPredict"]
services_db = db["servicesBN"]
journeys_db = db["journeysBN"]

# Loading pre-trained LGBM model and data encodings
model = joblib.load("models/lgbm_model.pkl")
target_maps = joblib.load("models/target_encodings.pkl")

uk_holidays = holidays.UK(subdiv="ENG")

# Enable CORS (Allow React frontend to access API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Request structure for delay prediction
class PredictRequest(BaseModel):
    service_id: int
    stop_name: str
    destination: str
    date: str
    time: str

def time_to_minutes(timestr: str) -> int:
    # Converting time to minutes
    h, m = map(int, timestr.split(":"))
    return h * 60 + m

def is_peak(mins: int, weekday: int) -> bool:
    # Defining peak hours (7-9am & 3-6pm on weekdays)
    if weekday >= 5: return False
    return (420 <= mins < 540) or (900 <= mins < 1080)

def get_day(date: str) -> int:
    # Getting the day of the week
    return datetime.fromisoformat(date).date().weekday()

# API ENDPOINTS
# ---------------------------------------------------------------------
@app.get("/")
def home():
    return {"message": "FastAPI is running!"}

@app.get("/get_services")
def get_services(query: str ):
    # Searching for services in MongoDB using regex
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

    # Building filter for MongoDB to get journeys around the specified time
    filter = {
        "service_id": req.service_id,
        "stop_name": req.stop_name,
        "destination": req.destination,
        "scheduled_mins": {"$gte": low, "$lte": high},
        "is_holiday": date in uk_holidays,
        "is_peak": is_peak(dep_mins, date.weekday()),
    }
    
    # MongoDB query - specifying the attributes to return
    retrieved_journeys_general = list(journeys_db.find(filter, {
        "_id": 0,
        "delay_mins": 1,
        "scheduled_mins": 1,
        "actual_mins": 1,
        "journey_id": 1
    }))

    # Building filter to find closest journey on the same day
    filter = {
        "service_id": req.service_id,
        "stop_name": req.stop_name,
        "destination": req.destination,
        "scheduled_mins": {"$gte": low, "$lte": high},
        "day_of_week": get_day(req.date),
    }

    # MongoDB - specifying the attributes to return
    retrieved_journeys_dated = list(journeys_db.find(filter, {
        "scheduled_dep": 1,
        "scheduled_mins": 1,
    }))

    if not retrieved_journeys_general:
        raise HTTPException(404, "No matching history found")
    
    # Finding closest journey on the specific day
    closest = min(retrieved_journeys_general, key=lambda doc: abs(doc["scheduled_mins"] - dep_mins))

    # Checking if such journey exists to prevent errors
    if retrieved_journeys_dated:
        closest_on_date = min(
            retrieved_journeys_dated,
            key=lambda doc: abs(doc["scheduled_mins"] - dep_mins)
        )
    else:
        closest_on_date = ""

    return {"closest": closest, "closest_on_date": closest_on_date}

@app.post("/predict_delay")
def predict_delay(req: PredictRequest):
    # Finding closest historical journeys
    closest_js = get_closest_journey(req)
    closest_j = closest_js["closest"]
    closest_j_with_date = closest_js["closest_on_date"]

    if not closest_j:
        raise HTTPException(404, "No historical journey found in window")
    
    # Getting the origin and destination from the route description
    svc = services_db.find_one({"_id": req.service_id})
    if not svc or "description" not in svc:
        raise HTTPException(500, "Service description missing")

    origin, destination = [p.strip() for p in svc["description"].split(" - ")]

    # Retrieving stop index
    sample = journeys_db.find_one(
        {"service_id": req.service_id, "stop_name": req.stop_name},
        {"stop_index": 1}
    )
    if not sample:
        raise HTTPException(404, f"Stop {req.stop_name!r} not found.")
    stop_idx = sample["stop_index"]

    # Processing time and date
    try:
        j_date = datetime.fromisoformat(req.date).date()
        sched_mins = time_to_minutes(req.time)
    except Exception as e:
        raise HTTPException(400, f"Invalid date/time: {e}")

    day_of_week = j_date.weekday()
    is_holiday = j_date in uk_holidays

    # Constructing features for the model
    try:
        # Extracting and preparing encoded categorical features
        scheduled_mins = closest_j.get("scheduled_mins", 720)  # default to 12:00 if missing
        origin_enc = target_maps["origin"].get(origin.strip(), 0)
        destination_enc = target_maps["destination"].get(destination.strip(), 0)
        stop_name_enc = target_maps["stop_name"].get(req.stop_name.strip(), 0)

        row = {
        "time_sin": [np.sin(2 * np.pi * scheduled_mins / 1440)],
        "time_cos": [np.cos(2 * np.pi * scheduled_mins / 1440)],
        "day_of_week": [day_of_week],
        "is_holiday": [is_holiday],
        "service_id": [req.service_id],
        "stop_index": [stop_idx],
        "origin_te": [origin_enc],
        "destination_te": [destination_enc],
        "stop_name_te": [stop_name_enc],
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to build feature vector: {e}")
    
    # Making prediction
    X = pd.DataFrame(row)
    try:
        prediction = model.predict(X)[0]
    except Exception as e:
        raise HTTPException(500, f"Prediction failed: {e}")
    
    if closest_j_with_date:
        scheduled_dep = closest_j_with_date["scheduled_dep"]
    else:
        scheduled_dep = ""

    return {
        "predicted_delay_mins": int(prediction),
        "scheduled_dep": scheduled_dep
    }

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
    
    # Iterating through first few journeys to find one that ends at the known destination
    journey_index = 0
    while (True):
        if journey_index > 5:
            return []

        journey = journeys[journey_index]
        journey_id = journey["id"]

        stops_resp = requests.get(
            f"https://bustimes.org/services/{service_id}/journeys/{journey_id}.json", timeout=10
        )
        stops_resp.raise_for_status()

        stops = [ stop["name"] for stop in stops_resp.json().get("stops", []) if stop.get("name")]

        # If the last stop is the intended destination or the first and last stops are the same (in the case of circular routes), break the loop and return the stops list
        if destination in stops[-1] or stops[0] == stops[-1]:
            break;
        journey_index += 1
 
    return stops

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)