#!/usr/bin/env python

# Kafka
from kafka import KafkaConsumer, KafkaProducer
from kafka import TopicPartition

# Voip
from tgvoip import VoIPServerConfig
from tgvoip_pyrogram import VoIPFileStreamService
from tgvoip import CallState

# Telegram
import pyrogram
from pyrogram.errors import FloodWait
import tgcrypto

# Logging
import logging

# Mongo
from pymongo import MongoClient
from bson.objectid import ObjectId

# OS lib
import os
import time as t
import json
import re
import asyncio
import pytz
from datetime import datetime, date, timedelta
import requests

from conf import configuration as conf

uri = conf.MONGODB_URI
number_workers = 1
cwd = os.getcwd()
PATH_SOUND = cwd + "/sounds/"
tzInfo = pytz.timezone(conf.TIME_ZONE)


# Update sound to DB
def update_sound(type, sound):
    try:
        logging.debug("CHECK SOUND:".format(sound))
        with MongoClient(uri) as client_db:
            sound_db = client_db[conf.MONGODB_DB]
            sound_db_col = sound_db[conf.MONGODB_DB_SOUND_COL]
            query_sound = {'type': type, 'sound': sound}
            if sound_db_col.find_one(query_sound) is None:
                logging.debug("UPDATE SOUND TO DB")
                create_sound(type, sound)
                sound_db_col.insert_one(query_sound)
                logging.debug("UPDATE SOUND TO DB DONE")
            else:
                logging.debug("SOUND IN DB")
                find_sound = find(type, sound)
                if find_sound is not True:
                    create_sound(type, sound)
    except Exception as exc:
        logging.getLogger().exception(
            "Error occurred when UPDATE SOUND: {}".format(exc)
        )


# Find sound on local
def find(type, sound):
    try:
        logging.debug("FIND SOUND IN LOCAL", sound)
        path = PATH_SOUND + type + "/"
        name = sound + ".raw"
        for root, dirs, files in os.walk(path):
            if name in files:
                logging.debug("FILE EXIST IN LOCAL")
                return True
            else:
                logging.debug("FILE NOT EXIST IN LOCAL")
                return False
    except Exception as exc:
        logging.getLogger().exception(
            "Error occurred when find file in local: {}".format(exc)
        )


# Get id telegram
def get_id_tele(owner_name):
    try:
        logging.debug("GET ID TELEGRAM")
        with MongoClient(uri) as client_db:
            auto_calling_db = client_db[conf.MONGODB_DB]
            social_account_col = auto_calling_db["social_account"]
            owner_id = owner_name.split("-")[0].lower()
            tele_number_query = {'id': owner_id}
            owner_tele_id = social_account_col.find_one(tele_number_query)[
                'telegram_id']
            logging.debug("GET ID TELEGRAM DONE: ".format(owner_tele_id))
            return owner_tele_id
    except TypeError as exc:

        logging.info("USER: {} NOT FOUND TELEGRAM ID".format(owner_name))
        owner_tele_id = "nonuser"
        return owner_tele_id
    except Exception as exc:
        logging.getLogger().exception(
            "Error occurred when get tele id: {}".format(exc)
        )


def get_owner_fullname(owner_name):
    try:
        logging.debug("GET FULLNAME")
        with MongoClient(uri) as client_db:
            auto_calling_db = client_db[conf.MONGODB_DB]
            social_account_col = auto_calling_db["social_account"]
            owner_id = owner_name.split("-")[0].lower()
            tele_number_query = {'id': owner_id}
            owner_full_name = social_account_col.find_one(tele_number_query)[
                'name']
            if owner_full_name is None:
                owner_full_name = "nonuser"
            logging.debug("GET ID FULLNAME DONE".format(owner_full_name))
            return owner_full_name
    except TypeError as exc:
        logging.info("USER: {} NOT FOUND FULLNAME".format(owner_name))
        owner_full_name = "nonuser"
        return owner_full_name
    except Exception as exc:
        logging.getLogger().exception(
            "Error occurred when get fullname: {}".format(exc)
        )


#  Create new sound:
def create_sound(type, sound):
    try:
        print("CREATE SOUND IN LOCAL", sound)
        if type == "host":
            os.system(PATH_SOUND + "create_host_sound.sh " +
                      "{}".format(sound) + " > /dev/null 2>&1")
            logging.debug("CREATE HOST SOUND DONE")
        elif type == "owner":
            os.system(PATH_SOUND + "create_owner_sound.sh " +
                      "{}".format(sound) + " > /dev/null 2>&1")
            logging.debug("CREATE OWNER SOUND DONE")
        elif type == "msg":
            os.system(PATH_SOUND + "create_msg_sound.sh " +
                      "{}".format(sound) + " > /dev/null 2>&1")
            logging.debug("CREATE MSG SOUND DONE")
    except Exception as exc:
        logging.getLogger().exception(
            "Error occurred when create sound: {}".format(exc)
        )


# Update to DB
def update_db(alert_id_db):
    try:
        logging.debug("UPDATE ALERT ID TO DB")
        newvalues = {"$set": {"action": "REVIEWED"}}
        with MongoClient(uri) as client_db:
            alert_db = client_db[conf.MONGODB_DB]
            alert_col = alert_db[conf.MONGODB_DB_COL]
            myquery = {'_id': ObjectId(alert_id_db)}
            alert_col.update_one(myquery, newvalues)
            logging.debug("UPDATE ALERT ID TO DB DONE")

    except Exception as exc:
        logging.getLogger().exception(
            "Error occurred when update alert id to DB: {}".format(exc)
        )


# Get session string to make call
def get_session_string():
    logging.debug("GET SESSION ID")
    session_string = ""
    api_id = ""
    api_hash = ""
    with MongoClient(uri) as client_db:
        session_db = client_db[conf.MONGODB_DB]
        session_col = session_db["session"]
        session_query = {'status': 1}
        session_update = {"$set": {'status': 2}}
        i = 0
        while True:
            session_query_result = session_col.find_one(session_query)
            if session_query_result is not None:
                session_col.update_one(session_query, session_update)
                session_string = session_query_result["session_string"]
                session_name = session_query_result["session_name"]
                api_id = session_query_result["api_id"]
                api_hash = session_query_result["api_hash"]
                logging.info("Call with session: {}".format(session_name))
                return session_string, api_id, api_hash
            elif i < int(conf.TIME_CALL):
                logging.debug("RETRY SESSION")
                i += 1
                t.sleep(1)
                continue
            elif i == int(conf.TIME_CALL):
                logging.debug("SESSION LIMIT")
                raise SessionLimit("SESSION LIMIT")


class SessionLimit(Exception):
    """Raised when the SESSION LIMIT"""
    pass


# Free session string when end call
def end_session(call_session_string_end):
    try:
        logging.debug("END SESSION")
        session_update = {"$set": {'status': 1}}
        with MongoClient(uri) as client_db:
            session_db = client_db[conf.MONGODB_DB]
            session_col = session_db["session"]
            session_query = {'session_string': call_session_string_end}
            session_col.update_one(session_query, session_update)
            t.sleep(2)
            logging.debug("CLEAR SESSION DONE")
    except Exception as exc:
        logging.getLogger().exception(
            "Error occurred when end session: {}".format(exc)
        )


#  Function call:
def make_call_telegram(msg_name, list_owner_name, alert_host,
                       alert_state, alert_id_msg, user_telegram):
    try:
        # Config Call
        # Config Bitrate
        logging.info("START CALL")
        VoIPServerConfig.set_bitrate_config(16000, 20000, 8000, 1000, 1000)
        call_session_string, api_id, api_hash = get_session_string()
        client = pyrogram.Client(call_session_string, api_id=api_id,
                                 api_hash=api_hash)
        loop = asyncio.get_event_loop()
        voip_service = VoIPFileStreamService(client, receive_calls=False)
        client.start()

        async def auto_call_telegram():
            global in_call
            global time_call
            time_call = 0
            in_call = True
            logging.info(""" Call to user: {},
                        WITH TELE_ID:  {}
                        """.format(list_owner_name, user_telegram))
            call = await voip_service.start_call(user_telegram)
            call.play(PATH_SOUND + 'default/xinchao.raw')
            call.play_on_hold([PATH_SOUND + "host/" +
                               alert_host +
                               ".raw", PATH_SOUND + "owner/" +
                               list_owner_name +
                               ".raw", PATH_SOUND + "state/state-" +
                               alert_state +
                               ".raw", PATH_SOUND + "msg/" +
                               msg_name + ".raw"])

            @call.on_call_state_changed
            def state_changed(call, state):
                global in_call
                global time_call
                if state == CallState.ESTABLISHED:
                    logging.info("USER ACCEPT")
                    update_db(alert_id_msg)
                    time_call = 0
                elif state == CallState.BUSY:
                    logging.info("USER BUSY")
                    in_call = False
                elif state == CallState.ENDED:
                    logging.info("USER END CALL")
                    in_call = False
                return in_call, time_call
            while in_call:
                await asyncio.sleep(1)
                logging.debug("TIME IN CALL: {}".format(time_call))
                time_call += 1
                if time_call == int(conf.TIME_CALL):
                    in_call = False
                    await call.discard_call()
                    await asyncio.sleep(1)
                    logging.info("DISCARD CALL")
        loop.run_until_complete(auto_call_telegram())
        logging.info("END CALL")
        end_session(call_session_string)
        t.sleep(1)
        client.stop()
        logging.info("STOP CLIENT")
    except SessionLimit as exc:
        logging.info("SessionLimit")
        logging.info("SEND RETRY MSG")
        logging.getLogger().exception(
            "Error when calling to {}: {}".format(list_owner_name, exc)
        )
    except FloodWait as e:
        end_session(call_session_string)
        # t.sleep(e.x)
        msg = "Flood wait for: {} seconds".format(e.x)
        logging.info("FloodWait")
        logging.info("SEND RETRY MSG")
        logging.getLogger().exception(
            "Flood wait for: {} seconds".format(e.x)
        )
    except Exception as exc:
        end_session(call_session_string)
        logging.info("SEND RETRY MSG")
        logging.getLogger().exception(
            "Error when calling to {}: {}".format(list_owner_name, exc)
        )


# Create connection Kafka
consumer = KafkaConsumer(conf.KAFKA_TOPIC_ALERT,
                         auto_offset_reset='latest',
                         bootstrap_servers=conf.KAFKA_SERVER,
                         group_id=conf.KAFKA_GROUP_CONSUMER,
                         enable_auto_commit=False,
                         session_timeout_ms=int(conf.SESSION_TIMEOUT_MS),
                         max_poll_records=int(conf.MAX_POLL_RECORDS),
                         heartbeat_interval_ms=int(conf.HEARTBEAT_INTERVAL_MS),
                         request_timeout_ms=int(conf.REQUEST_TIMEOUT_MS)
                         # max_poll_interval_ms=conf.MAX_POLL_INTERVAL_MS,
                         # api_version=(0, 10, 1),
                         # value_deserializer=lambda x: x
                         )

if __name__ == '__main__':
    while True:
        level_log = conf.MODE
        logging.basicConfig(
            format='{"time": "%(asctime)s", "level": "%(levelname)s", "module": "%(name)s", "detail": "%(message)s"}', level=level_log)
        for msg in consumer:
            logging.debug("RECEIVED NEW MESSAGE :{}".format(msg))
            received_msg = json.loads(msg.value)
            logging.info("RECEIVED NEW MESSAGE :{}".format(received_msg))
            # consumer.commit_async()
            consumer.commit()
            logging.info("COMMIT MESSAGE")

            # Filter msg
            alert = re.sub('\W', ' ', received_msg['msg'])
            alert_msg = alert.replace(" ", "_")
            owner_service = received_msg['owner'].lower()
            status = received_msg['status'].lower()
            time_create = received_msg['created'][:16]
            host = received_msg['host']
            state = received_msg['state'].lower()
            alert_id = received_msg['id']
            makecall = received_msg['makecall'].lower()

            # Check alert exist
            update_sound("msg", alert_msg)

            # Get telegram id
            list_owner_tele_id = []
            # Get fullname
            list_owner_full_name = []
            list_all_owner = owner_service.split(",")

            list_all_owner = list(set(list_all_owner))
            logging.debug("List all owner calling :{}".format(list_all_owner))
            for user_owner in list_all_owner:
                user = user_owner.strip()
                list_owner_tele_id.append(get_id_tele(user))
                owner_fullname = get_owner_fullname(user).replace(" ", "_")
                update_sound("owner", owner_fullname)
                list_owner_full_name.append(owner_fullname)

            # Remove duplicate user
            list_owner_tele_id = list(dict.fromkeys(list_owner_tele_id))
            list_owner_full_name = list(dict.fromkeys(list_owner_full_name))

            # Remove nonuser
            if 'nonuser' in list_owner_tele_id:
                list_owner_tele_id.remove('nonuser')
            if 'nonuser' in list_owner_full_name:
                list_owner_full_name.remove('nonuser')

            logging.info("LIST OWNER TELE ID: {}".format(list_owner_tele_id))
            logging.info("LIST OWNER FULLNAME: {}".format(
                list_owner_full_name))

            # Check host exist
            update_sound("host", host)

            # Filter and start call
            if status == 'firing' and makecall == 'true':
                for i in range(len(list_owner_tele_id)):
                    make_call_telegram(alert_msg, list_owner_full_name[i],
                                       host, state, alert_id,
                                       list_owner_tele_id[i])
                continue
            else:
                continue
