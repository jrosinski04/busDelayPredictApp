from pymongo import MongoClient

client = MongoClient("") # MISSING LINK
db = client["BusDelayPredict"]
collection = db["journeysBN"]

collection.delete_many({})