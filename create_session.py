import time
from pyrogram import Client
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

api_id = 12345 #Example
api_hash = "abvcdf" #Example
phone_number = "+84" #Example
uri = "mongodb://root:example@localhost:27017/?authMechanism=SCRAM-SHA-1"
userbot = input("Enter your BOT Session Name: ")
userbot_name = userbot.lower()
created_time = datetime.now()
with Client(
        userbot_name,
        api_id,
        api_hash,
        phone_number) as pyrogram:
    print("\nGenerating String session...\n")
    session_string = pyrogram.export_session_string()
    print(session_string)
    time.sleep(1)

    client_db = MongoClient(uri)
    session_db = client_db["auto-calling"]
    session_col = session_db["session"]
    session_query = {'session_string': session_string}
    if session_col.find_one(session_query) is not None:
        result_session_query = session_col.find_one(session_query)
        client_db.close()
        name_session = result_session_query['session_name']
        created_time_session = result_session_query['created']
        print("======> Session was created with name:", name_session, " at time: ", created_time_session, "\n")
    else:
        session_col.insert_one(session_query)
        status_session_value = {"$set": {"status": 1, "session_name": userbot_name,"api_id": api_id, "api_hash":api_hash, "phone_number": phone_number, "created": datetime.now()}}
        session_col.update_one(session_query, status_session_value)
        print("\nGenerating String DONE !!!\n")
        print("Session is added to DB")
        client_db.close()