import requests
from pymongo import MongoClient, UpdateOne

# Configuration parameters
OPERATORS = {"BNVB", "BNSM", "BNML", "BNGN", "BNFM", "BNDB"} # Bee Network operators (Vision Bus, Stagecoach, Metroline, Go North West, First Manchester, Diamond Bus)
PAGE_SIZE = 100 # Number of services per request

def load_services():
    # Connecting to MongoDB
    client = MongoClient("mongodb+srv://kuba08132004:Solo1998@jrcluster.nwclg.mongodb.net/BusDelayPredict")
    db = client.get_default_database()
    col = db.servicesBN

    # Base URL for the Bustimes API with North West region filter
    url = "https://bustimes.org/api/services/"
    params = {"page_size": PAGE_SIZE, "region_id":"NW"}

    ops = [] # List to hold update operations

    # Iterate through the pages of results until there is no next page
    while url:
        # Making GET request to current page URL
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        # Processing each service returned by API
        for svc in data.get("results", []):
            # Filter to Bee Network operators
            operators = svc.get("operator")
            operator = set(operators) & set(OPERATORS)

            if operator:
                # Building document with relevant info
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
        # Logging how many services were fetched from the page
        print(f"Fetched {len(data.get('results', []))} services from {url}")
        url = data.get("next") # Setting URL to next page
        params = None 

    # Upload collected data to MongoDB
    if ops:
        result = col.bulk_write(ops)
        print(f"Uploaded {result.upserted_count} services.")
    else:
        print("No services found!")
        
if __name__ == "__main__":
    load_services()