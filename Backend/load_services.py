
# load_services.py
# ----------------
# Fetch all services in a given region (paginated) and upsert into MongoDB

import requests
from pymongo import MongoClient, UpdateOne

# --- CONFIGURATION ---
MONGO_URI = "mongodb+srv://kuba08132004:Solo1998@jrcluster.nwclg.mongodb.net/BusDelayPredict"
OPERATORS = {"BNVB", "BNSM", "BNML", "BNGN", "BNFM", "BNDB"}
SLUG = "440-rochdale-syke-2"
PAGE_SIZE = 100  # API page size
# ---------------------


def load_services():
    client = MongoClient(MONGO_URI)
    db = client.get_default_database()
    #col = db.servicesBN
    col = db.servicesTEST

    url = "https://bustimes.org/api/services/"
    params = {"page_size": PAGE_SIZE, "slug":"440-rochdale-syke-2"}

    ops = []
    while url:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        for svc in data.get("results", []):
            # Filter to Bee Network operators
            slug = svc.get("slug")
            if (slug == SLUG):
                doc = {
                    "_id":         svc["id"],
                    "slug":        svc.get("slug"),
                    "number":      svc.get("line_name"),
                    "description": svc.get("description"),
                    "region_id":   svc.get("region_id"),
                    "mode":        svc.get("mode"),
                    "operator":    svc.get("operator"),
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