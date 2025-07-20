# backend/config.py
from pymongo import MongoClient
import os

# MONGO_URI = "mongodb://localhost:27017/"
# DB_NAME = "AIGoogle"

# client = MongoClient(MONGO_URI) # This line is already here
# db = client[DB_NAME]


MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "AIGoogle")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]