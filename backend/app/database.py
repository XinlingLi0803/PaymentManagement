from pymongo import MongoClient
import os

MONGO_URI = "mongodb://172.17.0.2:27017"
client = MongoClient(MONGO_URI)
db = client["payment_management"]
