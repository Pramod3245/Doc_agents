from pymongo import MongoClient
import os
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv("src/utils/.env")

# MongoDB configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/")
DATABASE_NAME = os.getenv("DATABASE_NAME", "docman_db")

# Global database client
global client, db
client = None
db = None

def connect_to_mongo():
    """Create database connection"""
    global client, db
    try:
        client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=3000)
        # Try to force connection on a request as the
        # connect=True parameter of MongoClient seems
        # to be useless here
        client.server_info()
        db = client[DATABASE_NAME]
        print(f"Connected to MongoDB at {MONGODB_URL}, database: {DATABASE_NAME}")
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
        db = None

def close_mongo_connection():
    """Close database connection"""
    global client
    if client:
        client.close()
        print("MongoDB connection closed.")

def get_database():
    """Get database instance"""
    global db
    if db is None:
        raise HTTPException(status_code=500, detail="Database connection is not established.")
    return db


