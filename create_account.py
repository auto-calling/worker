#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime


uri = "mongodb://root:example@localhost:27017/?authMechanism=SCRAM-SHA-1"
owner_id = "admin"  #Example
full_name = "Nguyễn Văn A"  #Example
telegram_id = "admin"   #Example

client_db = MongoClient(uri)
social_db = client_db["auto-calling"]
session_col = social_db["social_account"]
status_session_value = {"owner_id": owner_id, "telegram_id": telegram_id, "name":full_name , "created": datetime.now()}
session_col.insert_one(status_session_value)
print("Done")
client_db.close()