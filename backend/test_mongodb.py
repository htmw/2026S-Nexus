#!/usr/bin/env python3
"""Test MongoDB connection - run: python test_mongodb.py"""
import os
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("MONGODB_URI", "")
if not uri:
    print("ERROR: MONGODB_URI not set in .env")
    exit(1)

# Mask password for display
display_uri = uri
if "@" in uri:
    parts = uri.split("@")
    user_part = parts[0].split("//")[-1]
    if ":" in user_part:
        user = user_part.split(":")[0]
        display_uri = f"mongodb+srv://{user}:****@..." + parts[1].split("/")[-1].split("?")[0]
print(f"Testing: {display_uri}\n")

try:
    from pymongo import MongoClient
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    # Force connection
    client.admin.command("ping")
    db = client["mind_mirror"]
    coll = db["journals"]
    count = coll.count_documents({})
    print("SUCCESS: Connected to team MongoDB!")
    print(f"Database: mind_mirror, Collection: journals")
    print(f"Existing entries: {count}")
except Exception as e:
    print(f"FAILED: {e}")
    print("\nTo fix:")
    print("1. Go to https://cloud.mongodb.com → your project → Database Access")
    print("2. Add user or edit existing: username + password (S@nket07)")
    print("3. In .env set MONGODB_URI=mongodb+srv://USER:PASS@cluster0.abmnzeo.mongodb.net/mind_mirror?...")
    print("   (URL-encode @ in password as %40)")
    exit(1)
