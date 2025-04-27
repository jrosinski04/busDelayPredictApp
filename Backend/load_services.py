
# load_services.py
# ----------------
# Fetch all services in a given region (paginated) and upsert into MongoDB

import requests
from pymongo import MongoClient, UpdateOne

# --- CONFIGURATION ---
MONGO_URI = "mongodb+srv://kuba08132004:Solo1998@jrcluster.nwclg.mongodb.net/BusDelayPredict"
OPERATORS = {"BNVB", "BNSM", "BNML", "BNGN", "BNFM", "BNDB"}
PAGE_SIZE = 100  # API page size
# ---------------------


def load_services():
    client = MongoClient(MONGO_URI)
    db = client.get_default_database()
    col = db.servicesBN

    url = "https://bustimes.org/api/services/"
    params = {"page_size": PAGE_SIZE, "region_id":"NW"}

    ops = []
    while url:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        for svc in data.get("results", []):
            # Filter to Bee Network operators
            operators = svc.get("operator")
            operator = set(operators) & set(OPERATORS)

            if operator:
                doc = {
                    "_id":         svc["id"],
                    "slug":        svc.get("slug"),
                    "number":      svc.get("line_name"),
                    "description": svc.get("description"),
                    "region_id":   svc.get("region_id"),
                    "mode":        svc.get("mode"),
                    "operator":    list(operator)[0],
                }
                ops.append(
                    UpdateOne({"_id": doc["_id"]}, {"$set": doc}, upsert=True)
                )

        print(f"Fetched {len(data.get('results', []))} services from {url}")
        url = data.get("next")  # follow pagination
        params = None           # 'next' already includes query params

    if ops:
        result = col.bulk_write(ops)
        print(f"Upserted {result.upserted_count} services, modified {result.modified_count}")
    else:
        print("No Bee Network services found!")


if __name__ == "__main__":
    load_services()