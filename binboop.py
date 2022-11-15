import os
import time
import datetime
from dateutil import parser
import schedule
import requests
from dotenv import load_dotenv

load_dotenv()

alert_time = os.getenv('ALERT_TIME')
location_id = os.getenv('LOCATION_ID')
number_of_collections = 10
bin_collections_url = f'https://servicelayer3c.azure-api.net/wastecalendar/collection/search/{location_id}/?numberOfCollections={number_of_collections}'

round_types = {
    'ORGANIC': 'garden waste',
    'RECYCLE': 'recycling',
    'DOMESTIC': 'rubbish',
}

pushover_url = 'https://api.pushover.net/1/messages.json'
pushover_params = {
    "token": os.getenv('PUSHOVER_TOKEN'),
    "user": os.getenv('PUSHOVER_USER'),
}

# Helper functions for logging
def get_current_time():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def log(message):
    print(f"[{get_current_time()}] {message}")

# Send an alert via Pushover
def send_alert(payload):
    log("Sending alert")
    try:
        params = {**pushover_params, **payload}
        response = requests.post(pushover_url, params=params)
    except Exception as e:
        log(f"Error sending alert: {e}")

def check_bin_collections():
    log("Checking bin collection times")
    try:
        # Fetch the API data
        response = requests.get(url=bin_collections_url)
        data = response.json()

        # Parse the data from the next collection into friendly formats
        # As of November 2022, the API splits the collection types for one date
        # into multiple objects, with slightly different times in the date
        # and different collection types - so we need to scoop up a couple of
        # collections and check them together.
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        collections_for_tomorrow = []
        for collection in data['collections']:
            collection_date = parser.parse(collection['date']).date()
            # Check if the collection date is tomorrow (we want to be alerted
            # the night before)
            if collection_date == tomorrow:
                collection_types = [round_types[x] for x in collection['roundTypes']]
                collections_for_tomorrow.extend(collection_types)

        # If we have collections for tomorrow, join them into a string and send a message
        if collections_for_tomorrow:
            collection_types_string = ' and '.join(collections_for_tomorrow)
            payload = {
                "message": f"Don't forget to put the {collection_types_string} {'bins' if len(collection_types) > 1 else 'bin'} out tonight.",
            }
            send_alert(payload)
    except Exception as e:
        log(f"Error getting bin collection times: {e}")

schedule.every().day.at(alert_time).do(check_bin_collections)

log("BinBoop is running!")

# On start, send a Pushover message so we know that everything is working
startup_payload = {
    "message": "BinBoop is running!",
}
send_alert(startup_payload)

while True:
    schedule.run_pending()
    time.sleep(1)
