import requests, time
from datetime import datetime, timedelta
from pymongo import MongoClient, UpdateOne
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# CONFIGURATION PARAMETERS
MONGO_URI    = "mongodb+srv://kuba08132004:Solo1998@jrcluster.nwclg.mongodb.net/BusDelayPredict"
DB_NAME      = "BusDelayPredict"
SERVICES_COL = "servicesTEST"
JOURNEYS_COL = "journeysTEST"

START_DATE   = "2025-04-23"   
END_DATE     = "2025-04-23"   
PAGE_SIZE    = 100
BATCH_SIZE   = 100
PAUSE        = 15
# ----------------------------------------

def chunk_list(list, size):
    # Yields successive chunks of the set size
    for i in range(0, len(list), size):
        yield list[i:i+size]

def load_journeys():
    # Connecting to MongoDB and fetching the bus services
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    service_ids = [s["_id"] for s in db[SERVICES_COL].find({}, {"_id":1})]
    journeys_col = db[JOURNEYS_COL]

    # Configuring HTTP session with retry/backoff
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))

    # Setting up and parsing threshold dates
    start_date = datetime.fromisoformat(START_DATE).date()
    end_date   = datetime.fromisoformat(END_DATE).date()

    # Iterating over each service
    for svc_id in service_ids:
        print(f"\nProcessing service {svc_id}")

        # Configuring the API URL for listing the journies of the current bus service
        apiURL = f"https://bustimes.org/api/vehiclejourneys/?service={svc_id}"
        params = {"page_size": PAGE_SIZE}
        stop_paging = False
        total_for_service = 0

        # Getting all journey IDs for the current bus service within the date parameters
        journeys = []

        while apiURL and not stop_paging:
            # Fetching the journeys via the API
            apiResp = requests.get(apiURL, params=params, timeout=10)
            apiResp.raise_for_status()
            data = apiResp.json()

            # Iterating over each journey 
            for j in data.get("results", []):
                j_date = datetime.fromisoformat(j["datetime"]).date()

                # Skipping journeys newer than the END_dATE
                if j_date > end_date:
                    continue
                # Stopping paging once a journey before the START_DATE is found
                if j_date < start_date:
                    stop_paging = True
                    break

                # If the journey matches the date filter, the journey ID is saved
                journeys.append(j["id"])
            
            # Advancing to the next page
            apiURL = data.get("next")
            params = None # (the 'next' URL already contains query params)

        print(f" - {len(journeys)} journey IDs collected and batching in groups of {BATCH_SIZE}")

        # Processing the journeys in batches to control load
        operations = []

        for batch_num, batch in enumerate(chunk_list(journeys, BATCH_SIZE), 1):
            print(f" * Processing batch {batch_num} ({len(batch)} journeys)...")
            for jid in batch:

                # Fetching the detailed JSON for each journey
                detail = requests.get(f"https://bustimes.org/services/{svc_id}/journeys/{jid}.json", timeout=10).json()

                # Delaying the operation to control load
                time.sleep(0.4)

                stops = detail.get("stops", [])
                if not stops:
                    continue

                first = stops[0] # Origin of the journey
                last  = stops[-1] # Destination of the journey
                j_date  = datetime.fromisoformat(detail["datetime"]).date()

                # Iterating over all stops in the current journey
                for index, stop in enumerate(stops):

                    sched_dep = stop.get("aimed_departure_time") 
                    sched_mins = time_to_mins(sched_dep)

                    actual_dep_string = stop.get("actual_departure_time")
                    actual_dep = None
                    actual_mins = None
                    delay = None

                    # Parsing, correcting timezone and formatting the actual departure time
                    if actual_dep_string:
                        dt = datetime.fromisoformat(actual_dep_string.replace("Z", "+00:00")) + timedelta(hours=1)
                        actual_dep = dt.strftime("%H:%M")
                        actual_mins = time_to_mins(actual_dep)

                        # Calculate delay
                        delay = actual_mins - sched_mins

                    # Building the MongoDB document for the stop event
                    doc = {
                        "_id":           f"{svc_id}_{stop['id']}",
                        "service_id":    svc_id,
                        "journey_id":    jid,
                        "stop_index":    index,
                        "stop_name":     stop["name"],
                        "date":          j_date.isoformat(),
                        "origin":        first.get("name"),
                        "destination":   last.get("name"),
                        "scheduled_dep": sched_dep,
                        "scheduled_mins":sched_mins,
                        "actual_dep":    actual_dep,
                        "actual_mins":   actual_mins,
                        "delay_mins":    delay
                        "day_of_week":   get_day(j_date.isoformat())

                    }
                    operations.append(UpdateOne({"_id": doc["_id"]}, {"$set": doc}, upsert=True))
                    total_for_service += 1

            # Writing current batch to MongoDB to control local memory usage
            if operations:
                result = journeys_col.bulk_write(operations)
                print(f"     - batch {batch_num} wrote {result.upserted_count} upserts, {result.modified_count} updates")
                operations.clear()

            # Pausing before executing the next batch
            print(f"     - sleeping {PAUSE}s ...")
            time.sleep(PAUSE)

        print(f" FINISHED: Collected {total_for_service} journeys for {svc_id}")

def time_to_mins(timestr: str) -> int:
    # Converting date variable to minutes since midnight for easier calculation
    h, m = map(int, timestr.split(":"))
    return h * 60 + m

def get_day(date: str) -> int:
    # Getting the day of the week
    return datetime.fromisoformat(date).date().weekday()

if __name__ == "__main__":
    load_journeys()
