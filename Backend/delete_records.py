from pymongo import MongoClient

client = MongoClient("mongodb+srv://kuba08132004:Solo1998@jrcluster.nwclg.mongodb.net/BusDelayPredict")
db = client["BusDelayPredict"]
collection = db["servicesBN"]

collection.delete_many({})  # Deletes all documents in the collection