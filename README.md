- [Auto-calling-worker](#auto-calling-worker)
  - [Feature overview](#feature-overview)
  - [Building](#building)
  - [Running](#running)
  - [Event Call](#event-call)
  - [Format message queue kafka](#format-message-queue-kafka)
  - [Requirements](#requirements)
  - [How to start](#how-to-start)

# Auto-calling-worker

## Feature overview

- Worker receive message from Kafka queue and make call via Telegram

![image](image/worker.png)

## Building

- Building the Docker image

```
docker build .
```

## Running

Update ENV ```docker-compose.yml```

```
docker-compose up -d
```

## Event Call

- Filter msg, owner, host, state from kafka message
- Create local sound from receive message
- Mapping owner and id telegram in collection social_account from MongoDB
- Select session from MongoDB
- Make call to telegram and update status to MongoDB

## Format message queue kafka

```json
{
    "_id": "60a3f9449501d60008813aaa",
    "host": "192.168.199.199",
    "owner": "Admin",
    "state": "CRITICAL",
    "status": "FIRING",
    "msg": "Port 8080 down",
    "action": "PENDING",
    "status": "Firing",
    "created": "2021-12-12T12:12:12.409Z",
    "makecall":"true"
}
```

## Requirements
  - Python 3.5 or higher
  - PytgVoIP (listed as dependency)
  - Pyrogram (listed as dependency)

## How to start

- Install Pyrogram
  - The easiest way to install and upgrade Pyrogram to its latest stable version is by using pip:
    ```$ pip3 install -r requirements-script.txt```
  - Get your own Telegram API key (api_id, api_hash) from <https://my.telegram.org/apps>
  - Make sure MongoDB, Kafka, auto-calling-gateway was up
  - Get Telegram session manual:
    - Step 1: Update ```api_id```, ```api_hash```, ```phone_number``` to ```create_session.py```
    - Step 2: Update ```owner_id```, ```full_name```, ```telegram_id``` to ```create_account.py```
    - Step 4: Run ```python3 create_account.py```
    - Step 5: Run ```python3 create_session.py```
    - Step 6: Enter phone number
    - Step 7: Enter OTP
    - Step 8: Update the session string to collection ```session``` in MongoDB
    - Step 9: Start worker service ```docker-compose up -d```
    - Step 10: Send request to: "http://127.0.0.1/api/v1/make/event"
      ```
      curl --location --request POST 'http://127.0.0.1/api/v1/make/event' \
      --header 'Authorization: Bearer change_me'                          \
      --header 'Content-Type: application/json' --data-raw '{
          "host": "Test",
          "owner": "admin",
          "state": "CRITICAL",
          "msg":"Port 8080 down",
          "created":"2021-12-12 12:12:12",
          "service": "Test",
          "status": "Firing",
          "action": "PENDING",
          "makecall": "True"
      }'
      ```